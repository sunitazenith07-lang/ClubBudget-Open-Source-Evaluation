from __future__ import annotations


def new_account(account_id: str) -> dict:
    """Create a new loyalty account structure."""
    return {
        "account_id": str(account_id) if account_id is not None else "",
        "points_balance": 0,
        "processed_event_ids": [],
        "transactions": {},
        "ledger": [],
    }
