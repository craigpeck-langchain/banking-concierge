"""Unit tests for the open_account tool."""

from __future__ import annotations

import pytest

from concierge.tools import open_account


def test_open_account_happy_path():
    result = open_account.invoke(
        {
            "customer_id": "CUST-0001",
            "account_type": "Prime Checking",
            "opening_deposit": 500.0,
            "funding_source_account": "1234",
        }
    )
    assert result["status"] == "submitted"
    assert result["application_id"].startswith("APP-")
    assert len(result["application_id"]) == len("APP-") + 8
    assert "estimated_open_time" in result


def test_open_account_rejects_unknown_account_type():
    with pytest.raises(ValueError, match="not supported"):
        open_account.invoke(
            {
                "customer_id": "CUST-0001",
                "account_type": "Crypto Checking",
                "opening_deposit": 1000.0,
                "funding_source_account": "1234",
            }
        )


def test_open_account_rejects_under_minimum_deposit():
    with pytest.raises(ValueError, match="below the minimum"):
        open_account.invoke(
            {
                "customer_id": "CUST-0001",
                "account_type": "Prime Checking",
                "opening_deposit": 1.0,
                "funding_source_account": "1234",
            }
        )
