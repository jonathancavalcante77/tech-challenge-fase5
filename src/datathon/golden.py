"""Casos de referência usados para explicar decisões da política."""

from __future__ import annotations

GOLDEN_SET = (
    {
        "case_id": "recent_mens_web",
        "recency": 2,
        "history": 420.0,
        "mens": 1,
        "womens": 0,
        "newbie": 0,
        "zip_code": "Urban",
        "channel": "Web",
    },
    {
        "case_id": "recent_womens_multichannel",
        "recency": 3,
        "history": 610.0,
        "mens": 0,
        "womens": 1,
        "newbie": 0,
        "zip_code": "Surburban",
        "channel": "Multichannel",
    },
    {
        "case_id": "middle_mixed_web",
        "recency": 5,
        "history": 780.0,
        "mens": 1,
        "womens": 1,
        "newbie": 0,
        "zip_code": "Urban",
        "channel": "Web",
    },
    {
        "case_id": "old_mens_phone",
        "recency": 9,
        "history": 260.0,
        "mens": 1,
        "womens": 0,
        "newbie": 1,
        "zip_code": "Rural",
        "channel": "Phone",
    },
    {
        "case_id": "old_womens_web",
        "recency": 11,
        "history": 330.0,
        "mens": 0,
        "womens": 1,
        "newbie": 1,
        "zip_code": "Urban",
        "channel": "Web",
    },
)


def case_context(case: dict[str, object]) -> dict[str, object]:
    """Remove o identificador editorial antes da inferência."""

    return {key: value for key, value in case.items() if key != "case_id"}
