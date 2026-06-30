"""Tests for concierge tools."""

from __future__ import annotations

import pytest

from concierge.tools import lookup_customer_by_card


def test_lookup_customer_by_card_match():
    result = lookup_customer_by_card.invoke({"card_last_four": "4242"})
    assert result["match"] is True
    assert result["customer_id"] == "CUST-0001"
    assert result["name"] == "Alex Rivera"


def test_lookup_customer_by_card_no_match():
    result = lookup_customer_by_card.invoke({"card_last_four": "0000"})
    assert result == {"match": False}


def test_lookup_customer_by_card_invalid_input():
    with pytest.raises(ValueError):
        lookup_customer_by_card.invoke({"card_last_four": "42"})
    with pytest.raises(ValueError):
        lookup_customer_by_card.invoke({"card_last_four": "abcd"})
    with pytest.raises(ValueError):
        lookup_customer_by_card.invoke({"card_last_four": "42424"})
