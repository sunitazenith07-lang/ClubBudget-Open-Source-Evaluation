from __future__ import annotations

import pytest
from models import new_account
from service import calculate_points, apply_reward_event, flag_repeat_transactions


class TestCalculatePointsRegression:
    def test_non_int_types_award_zero(self):
        """Ensure bool, float, string, None, and collection types are safely rejected."""
        assert calculate_points(True, 1) == 0  # bool is subclass of int in Python
        assert calculate_points(False, 1) == 0
        assert calculate_points(10000.0, 1) == 0
        assert calculate_points("10000", 1) == 0
        assert calculate_points(None, 1) == 0
        assert calculate_points([], 1) == 0
        assert calculate_points({}, 1) == 0

    def test_bonus_percent_none_defaults_to_zero(self):
        """Passing bonus_percent=None should default to 0% bonus, not fail or return 0."""
        assert calculate_points(10000, 1, bonus_percent=None) == 1
        assert calculate_points(50000, 2, bonus_percent=None) == 10

    def test_invalid_rules_award_zero(self):
        """Negative or non-integer rules must not produce points."""
        assert calculate_points(20000, -1, 0, None) == 0
        assert calculate_points(20000, 1, -10, None) == 0
        assert calculate_points(20000, 1, 0, -5) == 0
        assert calculate_points(20000, True, 0, None) == 0
        assert calculate_points(20000, 1, True, None) == 0
        assert calculate_points(20000, 1, 0, True) == 0

    def test_paise_boundary_rounding(self):
        """Floor division must truncate fractions of 100 rupees (10000 paise)."""
        assert calculate_points(9999, 1) == 0
        assert calculate_points(10000, 1) == 1
        assert calculate_points(10001, 1) == 1
        assert calculate_points(19999, 1) == 1
        assert calculate_points(20000, 1) == 2

    def test_large_bonus_and_strict_cap(self):
        """Large bonus percent > 100% and strict cap points application."""
        # Base: 30000 // 10000 = 3 * 2 = 6. Bonus: 6 * 250 // 100 = 15. Cap: 10 => 10.
        assert calculate_points(30000, 2, 150, 10) == 10
        # Cap 0 must always yield 0
        assert calculate_points(30000, 2, 150, 0) == 0


class TestApplyRewardEventRegression:
    def test_missing_event_or_transaction_id_is_safe(self):
        """Events without event_id or transaction_id should not modify account."""
        acc = new_account("ACCT-1")
        res1 = apply_reward_event(acc, {"type": "purchase_captured", "amount_paise": 10000}, {})
        assert res1["points_balance"] == 0
        assert res1["transactions"] == {}
        assert res1["ledger"] == []
        assert res1["processed_event_ids"] == []

        res2 = apply_reward_event(acc, {"event_id": "E1", "type": "purchase_captured", "amount_paise": 10000}, {})
        assert res2["points_balance"] == 0
        assert res2["transactions"] == {}

    def test_corrupted_or_null_account_fields_handled_safely(self):
        """Account with None/negative values should be sanitized without throwing TypeError."""
        corrupted_acc = {
            "account_id": "ACCT-1",
            "points_balance": None,
            "processed_event_ids": None,
            "transactions": None,
            "ledger": None,
        }
        res = apply_reward_event(
            corrupted_acc,
            {"event_id": "E1", "type": "purchase_captured", "transaction_id": "TX-1", "amount_paise": 10000},
            {"points_per_100_rupees": 1},
        )
        assert res["points_balance"] == 1
        assert res["processed_event_ids"] == ["E1"]
        assert len(res["ledger"]) == 1

    def test_cross_account_event_rejected(self):
        """Events explicitly targeting a different account_id must be ignored."""
        acc = new_account("ACCT-1001")
        event = {
            "event_id": "E1",
            "account_id": "ACCT-2002",
            "type": "purchase_captured",
            "transaction_id": "TX-1",
            "amount_paise": 50000,
        }
        res = apply_reward_event(acc, event, {"points_per_100_rupees": 1})
        assert res["points_balance"] == 0
        assert res["transactions"] == {}
        assert res["ledger"] == []

    def test_rules_with_none_values_use_proper_defaults(self):
        """Rule dictionaries with explicit None values should default safely."""
        rules = {"points_per_100_rupees": None, "bonus_percent": None, "cap_points": None}
        acc = new_account("ACCT-1")
        event = {"event_id": "E1", "type": "purchase_captured", "transaction_id": "TX-1", "amount_paise": 20000}
        res = apply_reward_event(acc, event, rules)
        # 20000 // 10000 = 2 * 1 (default per) = 2 points
        assert res["points_balance"] == 2

    def test_cumulative_partial_refunds_and_over_refund(self):
        """Test sequence: purchase -> partial refund 1 -> partial refund 2 -> excess refund."""
        rules = {"points_per_100_rupees": 1}
        acc = new_account("ACCT-1")

        # Purchase: 1000 rupees (100000 paise) -> 10 points
        acc = apply_reward_event(
            acc,
            {"event_id": "E1", "type": "purchase_captured", "transaction_id": "TX-1", "amount_paise": 100000},
            rules,
        )
        assert acc["points_balance"] == 10
        assert acc["transactions"]["TX-1"]["awarded_points"] == 10
        assert len(acc["ledger"]) == 1

        # Partial refund 1: 400 rupees (40000 paise) -> 4 points reversed
        acc = apply_reward_event(
            acc,
            {"event_id": "E2", "type": "refund_processed", "transaction_id": "TX-1", "amount_paise": 40000},
            rules,
        )
        assert acc["points_balance"] == 6
        assert acc["transactions"]["TX-1"]["refunded_paise"] == 40000
        assert acc["transactions"]["TX-1"]["reversed_points"] == 4
        assert acc["ledger"][-1] == {"event_id": "E2", "type": "refund_processed", "points_delta": -4}

        # Partial refund 2: 600 rupees (60000 paise) -> remaining 6 points reversed
        acc = apply_reward_event(
            acc,
            {"event_id": "E3", "type": "refund_processed", "transaction_id": "TX-1", "amount_paise": 60000},
            rules,
        )
        assert acc["points_balance"] == 0
        assert acc["transactions"]["TX-1"]["refunded_paise"] == 100000
        assert acc["transactions"]["TX-1"]["reversed_points"] == 10
        assert acc["ledger"][-1] == {"event_id": "E3", "type": "refund_processed", "points_delta": -6}

        # Excess refund 3: 1 paise more -> rejected without changing account
        acc_excess = apply_reward_event(
            acc,
            {"event_id": "E4", "type": "refund_processed", "transaction_id": "TX-1", "amount_paise": 1},
            rules,
        )
        assert acc_excess["points_balance"] == 0
        assert acc_excess["transactions"]["TX-1"]["refunded_paise"] == 100000
        assert len(acc_excess["ledger"]) == 3
        assert "E4" not in acc_excess["processed_event_ids"]

    def test_refund_event_idempotency(self):
        """Replaying a refund event must not reverse points multiple times."""
        rules = {"points_per_100_rupees": 1}
        acc = new_account("ACCT-1")
        acc = apply_reward_event(
            acc,
            {"event_id": "E1", "type": "purchase_captured", "transaction_id": "TX-1", "amount_paise": 100000},
            rules,
        )
        refund_event = {"event_id": "E2", "type": "refund_processed", "transaction_id": "TX-1", "amount_paise": 50000}
        acc1 = apply_reward_event(acc, refund_event, rules)
        acc2 = apply_reward_event(acc1, refund_event, rules)

        assert acc2["points_balance"] == 5
        assert acc2["transactions"]["TX-1"]["refunded_paise"] == 50000
        assert len(acc2["ledger"]) == 2
        assert acc2["processed_event_ids"] == ["E1", "E2"]

    def test_refund_balance_never_negative(self):
        """Even if balance was modified externally, refund reversal delta cannot make balance negative."""
        rules = {"points_per_100_rupees": 1}
        acc = new_account("ACCT-1")
        acc = apply_reward_event(
            acc,
            {"event_id": "E1", "type": "purchase_captured", "transaction_id": "TX-1", "amount_paise": 100000},
            rules,
        )
        # Artificially simulate spent balance: only 2 points left
        acc["points_balance"] = 2
        refund_event = {"event_id": "E2", "type": "refund_processed", "transaction_id": "TX-1", "amount_paise": 100000}
        res = apply_reward_event(acc, refund_event, rules)
        assert res["points_balance"] == 0
        assert res["ledger"][-1]["points_delta"] == -2


class TestFlagRepeatTransactionsRegression:
    def test_non_list_or_empty_transactions(self):
        """Gracefully handle empty, None, or invalid transaction container."""
        assert flag_repeat_transactions([]) == []
        assert flag_repeat_transactions(None) == []  # type: ignore
        assert flag_repeat_transactions("invalid") == []  # type: ignore

    def test_threshold_none_or_invalid_defaults_to_two(self):
        """Threshold None, bool, or invalid type defaults safely to 2."""
        rows = [{"transaction_id": str(i), "account_id": "A", "date": "D", "amount_paise": 1000} for i in range(3)]
        # 3 items > threshold 2 -> flagged
        assert len(flag_repeat_transactions(rows, threshold=None)) == 1
        assert len(flag_repeat_transactions(rows, threshold=True)) == 1

    def test_deterministic_sorting(self):
        """Groups are ordered deterministically by key."""
        txs = [
            {"transaction_id": "T2", "account_id": "B", "date": "2026-10-02", "amount_paise": 500},
            {"transaction_id": "T1", "account_id": "A", "date": "2026-10-01", "amount_paise": 500},
            {"transaction_id": "T3", "account_id": "B", "date": "2026-10-02", "amount_paise": 500},
            {"transaction_id": "T4", "account_id": "A", "date": "2026-10-01", "amount_paise": 500},
        ]
        flags = flag_repeat_transactions(txs, threshold=1)
        assert len(flags) == 2
        assert flags[0]["account_id"] == "A"
        assert flags[1]["account_id"] == "B"
