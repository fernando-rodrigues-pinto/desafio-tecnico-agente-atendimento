from datetime import datetime

import pytest

from src.agent import build_system_prompt, store_status


@pytest.mark.parametrize(
    "moment, expected",
    [
        ("2026-03-25T10:00", {"open": True, "reopens": None}),  # Wednesday
        ("2026-03-25T09:00", {"open": True, "reopens": None}),
        ("2026-03-25T08:59", {"open": False, "reopens": "quarta-feira às 09:00"}),
        ("2026-03-25T18:00", {"open": False, "reopens": "quinta-feira às 09:00"}),
        ("2026-03-28T12:59", {"open": True, "reopens": None}),  # Saturday
        ("2026-03-28T13:00", {"open": False, "reopens": "segunda-feira às 09:00"}),
        ("2026-03-29T15:00", {"open": False, "reopens": "segunda-feira às 09:00"}),  # Sunday
        ("2026-03-27T20:00", {"open": False, "reopens": "sábado às 09:00"}),  # Friday night
    ],
)
def test_store_status(moment, expected):
    assert store_status(datetime.fromisoformat(moment)) == expected


def test_system_prompt_includes_date_and_store_status():
    prompt = build_system_prompt(datetime(2026, 3, 29, 15, 0))
    assert "domingo, 29/03/2026, 15:00" in prompt
    assert "A loja está fechada agora; reabre segunda-feira às 09:00." in prompt
