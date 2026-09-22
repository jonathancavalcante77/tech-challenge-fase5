"""API e interface web da demonstração local."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
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

    configured = Settings(
        data_path=Path(os.getenv("DATA_PATH", "data/raw/hillstrom.csv")),
        state_path=Path(os.getenv("STATE_PATH", "state/policy.json")),
        database_path=Path(os.getenv("DATABASE_PATH", "state/decisions.db")),
        policy_mode=os.getenv("POLICY_MODE", "mutable"),
        app_env=os.getenv("APP_ENV", "local"),
        mlflow_tracking_uri=os.getenv("MLFLOW_TRACKING_URI", "sqlite:///mlruns/mlflow.db"),
    )
    configured.ensure_directories()
    service = RecommendationService(configured.state_path, configured.database_path, configured.policy_mode)
    application = FastAPI(
        title="Adaptive Offers Lab",
        description="Demonstração reproduzível de experimentação adaptativa.",
        version="0.1.0",
    )
    templates = Jinja2Templates(directory="app/templates")
    application.mount("/static", StaticFiles(directory="app/static"), name="static")
    application.state.service = service

    @application.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def home(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request=request, name="index.html", context={"catalog": catalog_payload()})

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "environment": configured.app_env}

    @application.get("/metadata")
    async def metadata() -> dict[str, object]:
        return {**service.metadata(), "catalog": catalog_payload()}

    @application.post("/recommend")
    async def recommend(payload: ContextRequest) -> dict[str, object]:
        return service.recommend(payload.model_dump())

    @application.post("/feedback")
    async def feedback(payload: FeedbackRequest) -> dict[str, object]:
        try:
            return service.feedback(payload.decision_id, payload.reward)
        except PermissionError as error:
            raise HTTPException(status_code=403, detail=str(error)) from error
        except KeyError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        except ValueError as error:
            raise HTTPException(status_code=409, detail=str(error)) from error

    @application.get("/metrics", response_class=PlainTextResponse)
    async def metrics() -> str:
        stats = service.metadata()["store"]
        return (
            "# HELP adaptive_offers_decisions_total Decisões persistidas localmente.\n"
            "# TYPE adaptive_offers_decisions_total counter\n"
            f"adaptive_offers_decisions_total {stats['decisions']}\n"
            "# HELP adaptive_offers_feedback_total Feedbacks persistidos localmente.\n"
            "# TYPE adaptive_offers_feedback_total counter\n"
            f"adaptive_offers_feedback_total {stats['feedbacks']}\n"
        )

    return application


app = create_app()
