"""Regression tests for account_lookup PII masking."""

from __future__ import annotations

from concierge.tools import account_lookup


def test_account_lookup_masks_sensitive_fields_by_default():
    result = account_lookup.invoke({"customer_id": "CUST-0001"})
    text = str(result)
    assert "552-19" not in text
    assert "4242 4242 4242 4242" not in text


def test_account_lookup_include_unmasked_returns_raw_record():
    result = account_lookup.invoke(
        {"customer_id": "CUST-0001", "include_unmasked": True}
    )
    text = str(result)
    assert "552-19" in text
    assert "4242 4242 4242 4242" in text
