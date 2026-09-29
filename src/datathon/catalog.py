"""Catálogo de ações exibidas na aplicação."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Offer:
    """Descrição de uma ação de campanha."""

    key: str
    label: str
    description: str


OFFERS = (
    Offer(
        "mens_email",
        "E-mail da categoria masculina",
        "Campanha de produtos da categoria masculina.",
    ),
    Offer(
        "womens_email",
        "E-mail da categoria feminina",
        "Campanha de produtos da categoria feminina.",
    ),
    Offer("no_email", "Sem envio de e-mail", "Nenhuma campanha é enviada nesta rodada."),
)

ACTION_KEYS = tuple(offer.key for offer in OFFERS)
ACTION_LABELS = {offer.key: offer.label for offer in OFFERS}
ACTION_INDEX = {key: index for index, key in enumerate(ACTION_KEYS)}

DATASET_TO_ACTION = {
    "Mens E-Mail": "mens_email",
    "Womens E-Mail": "womens_email",
    "No E-Mail": "no_email",
}


def catalog_payload() -> list[dict[str, str]]:
    """Retorna o catálogo em formato seguro para JSON."""

    return [offer.__dict__.copy() for offer in OFFERS]
