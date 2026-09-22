"""API e interface web da demonstração local."""

from __future__ import annotations

import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)
from pydantic import BaseModel, ConfigDict, Field

from datathon.catalog import catalog_payload
from datathon.config import Settings
from datathon.service import RecommendationService


class ContextRequest(BaseModel):
    """Contexto mínimo permitido para a recomendação."""

    model_config = ConfigDict(extra="forbid")

    recency: int = Field(ge=1, le=12)
    history: float = Field(ge=0)
    mens: int = Field(ge=0, le=1)
    womens: int = Field(ge=0, le=1)
    newbie: int = Field(ge=0, le=1)
    zip_code: str = Field(min_length=1, max_length=20)
    channel: str = Field(min_length=1, max_length=20)


class FeedbackRequest(BaseModel):
    """Resultado binário de uma decisão demonstrada."""

    model_config = ConfigDict(extra="forbid")

    decision_id: str = Field(min_length=1, max_length=80)
    reward: int = Field(ge=0, le=1)


def create_app() -> FastAPI:
    """Cria uma instância isolada para a aplicação e para os testes."""

    configured = Settings.from_env()
    configured.ensure_directories()
    service = RecommendationService(
        configured.state_path,
        configured.snapshot_path,
        configured.database_path,
        configured.policy_mode,
    )
    application = FastAPI(
        title="Adaptive Offers Lab",
        description="Demonstração reproduzível de experimentação adaptativa.",
        version="0.1.0",
    )
    templates = Jinja2Templates(directory="app/templates")
    application.mount("/static", StaticFiles(directory="app/static"), name="static")
    application.state.service = service
    registry = CollectorRegistry()
    request_count = Counter(
        "adaptive_offers_http_requests_total",
        "Requisições HTTP processadas.",
        ["method", "path", "status"],
        registry=registry,
    )
    request_latency = Histogram(
        "adaptive_offers_http_request_duration_seconds",
        "Latência HTTP em segundos.",
        ["method", "path"],
        registry=registry,
    )
    decisions = Counter(
        "adaptive_offers_recommendations_total",
        "Recomendações emitidas pela política.",
        ["action", "exploration"],
        registry=registry,
    )
    feedbacks = Counter(
        "adaptive_offers_feedback_events_total",
        "Feedbacks recebidos pelo serviço.",
        ["reward", "status"],
        registry=registry,
    )
    posterior_segments = Gauge(
        "adaptive_offers_policy_segments",
        "Segmentos presentes no estado Bayesiano.",
        registry=registry,
    )
    posterior_segments.set(len(service.policy.posterior()))

    @application.middleware("http")
    async def observe_http(request: Request, call_next):
        started_at = time.perf_counter()
        response = await call_next(request)
        route = request.scope.get("route")
        path = getattr(route, "path", "unmatched")
        request_count.labels(request.method, path, str(response.status_code)).inc()
        request_latency.labels(request.method, path).observe(time.perf_counter() - started_at)
        return response

    @application.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def home(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request, name="index.html", context={"catalog": catalog_payload()}
        )

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "environment": configured.app_env}

    @application.get("/metadata")
    async def metadata() -> dict[str, object]:
        return {**service.metadata(), "catalog": catalog_payload()}

    @application.post("/recommend")
    async def recommend(payload: ContextRequest) -> dict[str, object]:
        result = service.recommend(payload.model_dump())
        decisions.labels(str(result["action"]), str(bool(result["exploration"])).lower()).inc()
        posterior_segments.set(len(service.policy.posterior()))
        return result

    @application.post("/feedback")
    async def feedback(payload: FeedbackRequest) -> dict[str, object]:
        try:
            result = service.feedback(payload.decision_id, payload.reward)
            feedbacks.labels(str(payload.reward), str(result["status"])).inc()
            return result
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @application.get("/metrics", response_class=PlainTextResponse)
    async def metrics() -> PlainTextResponse:
        return PlainTextResponse(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)

    return application


app = create_app()
