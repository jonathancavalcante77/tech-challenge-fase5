from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture
def context() -> dict[str, object]:
    return {
        "recency": 3,
        "history": 350.0,
        "mens": 1,
        "womens": 0,
        "newbie": 0,
        "zip_code": "Urban",
        "channel": "Web",
    }


@pytest.fixture
def logged_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"recency": 2, "history": 100.0, "mens": 1, "womens": 0, "newbie": 0, "zip_code": "Urban", "channel": "Web", "action": "mens_email", "conversion": 1},
            {"recency": 8, "history": 80.0, "mens": 0, "womens": 1, "newbie": 1, "zip_code": "Rural", "channel": "Phone", "action": "womens_email", "conversion": 1},
            {"recency": 5, "history": 200.0, "mens": 1, "womens": 1, "newbie": 0, "zip_code": "Surburban", "channel": "Web", "action": "no_email", "conversion": 0},
            {"recency": 10, "history": 50.0, "mens": 0, "womens": 0, "newbie": 1, "zip_code": "Urban", "channel": "Multichannel", "action": "mens_email", "conversion": 0},
        ]
    )
