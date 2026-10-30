import pytest
from models import new_account
from service import (
    calculate_points,
    apply_reward_event,
    flag_repeat_transactions,
    generate_account_statement_csv,
)


def test_refund_event_replay_is_idempotent():
    rules = {"points_per_100_rupees": 1}
    acct = new_account("ACCT-REG-1")
    acct = apply_reward_event(
        acct,
        {"event_id": "P-1", "type": "purchase_captured", "transaction_id": "T-1", "amount_paise": 100000},
        rules,
    )
    assert acct["points_balance"] == 10

    refund_event = {"event_id": "R-1", "type": "refund_processed", "transaction_id": "T-1", "amount_paise": 50000}
    acct = apply_reward_event(acct, refund_event, rules)
    assert acct["points_balance"] == 5
    assert acct["transactions"]["T-1"]["reversed_points"] == 5
    assert len(acct["ledger"]) == 2

    # Replay identical refund event
    replayed = apply_reward_event(acct, refund_event, rules)
    assert replayed["points_balance"] == 5
    assert replayed["transactions"]["T-1"]["reversed_points"] == 5
    assert replayed["transactions"]["T-1"]["refunded_paise"] == 50000
    assert replayed["processed_event_ids"] == ["P-1", "R-1"]
    assert len(replayed["ledger"]) == 2


def test_cumulative_partial_refunds_and_over_refund_rejection():
    rules = {"points_per_100_rupees": 1}
    acct = new_account("ACCT-REG-2")
    acct = apply_reward_event(
        acct,
        {"event_id": "P-1", "type": "purchase_captured", "transaction_id": "T-1", "amount_paise": 100000},
        rules,
    )
    assert acct["points_balance"] == 10

    # First partial refund: 30000 paise (30%)
    acct = apply_reward_event(
        acct,
        {"event_id": "R-1", "type": "refund_processed", "transaction_id": "T-1", "amount_paise": 30000},
        rules,
    )
    assert acct["points_balance"] == 7
    assert acct["transactions"]["T-1"]["reversed_points"] == 3
    assert acct["transactions"]["T-1"]["refunded_paise"] == 30000

    # Second partial refund: 70000 paise (remaining 70%)
    acct = apply_reward_event(
        acct,
        {"event_id": "R-2", "type": "refund_processed", "transaction_id": "T-1", "amount_paise": 70000},
        rules,
    )
    assert acct["points_balance"] == 0
    assert acct["transactions"]["T-1"]["reversed_points"] == 10
    assert acct["transactions"]["T-1"]["refunded_paise"] == 100000

    # Third refund attempt: 1 paise (over-refund)
    over = apply_reward_event(
        acct,
        {"event_id": "R-3", "type": "refund_processed", "transaction_id": "T-1", "amount_paise": 1},
        rules,
    )
    assert over["points_balance"] == 0
    assert over["transactions"]["T-1"]["refunded_paise"] == 100000
    assert "R-3" not in over["processed_event_ids"]
    assert len(over["ledger"]) == 3


def test_proportional_integer_truncation_across_multiple_refunds():
    rules = {"points_per_100_rupees": 1}
    acct = new_account("ACCT-REG-3")
    # 30000 paise awards 3 points
    acct = apply_reward_event(
        acct,
        {"event_id": "P-1", "type": "purchase_captured", "transaction_id": "T-1", "amount_paise": 30000},
        rules,
    )
    assert acct["points_balance"] == 3

    # Refund 10000 paise: (3 * 10000) // 30000 = 1 point reversed
    acct = apply_reward_event(
        acct,
        {"event_id": "R-1", "type": "refund_processed", "transaction_id": "T-1", "amount_paise": 10000},
        rules,
    )
    assert acct["points_balance"] == 2
    assert acct["transactions"]["T-1"]["reversed_points"] == 1

    # Refund another 10000 paise: (3 * 20000) // 30000 = 2 points total, delta = 1
    acct = apply_reward_event(
        acct,
        {"event_id": "R-2", "type": "refund_processed", "transaction_id": "T-1", "amount_paise": 10000},
        rules,
    )
    assert acct["points_balance"] == 1
    assert acct["transactions"]["T-1"]["reversed_points"] == 2

    # Final refund 10000 paise: (3 * 30000) // 30000 = 3 points total, delta = 1
    acct = apply_reward_event(
        acct,
        {"event_id": "R-3", "type": "refund_processed", "transaction_id": "T-1", "amount_paise": 10000},
        rules,
    )
    assert acct["points_balance"] == 0
    assert acct["transactions"]["T-1"]["reversed_points"] == 3


def test_zero_awarded_purchase_refund_safety():
    rules = {"points_per_100_rupees": 1}
    acct = new_account("ACCT-REG-4")
    # Sub-100 rupee purchase (5000 paise) awards 0 points
    acct = apply_reward_event(
        acct,
        {"event_id": "P-1", "type": "purchase_captured", "transaction_id": "T-1", "amount_paise": 5000},
        rules,
    )
    assert acct["points_balance"] == 0
    assert acct["transactions"]["T-1"]["awarded_points"] == 0

    # Full refund of 5000 paise
    acct = apply_reward_event(
        acct,
        {"event_id": "R-1", "type": "refund_processed", "transaction_id": "T-1", "amount_paise": 5000},
        rules,
    )
    assert acct["points_balance"] == 0
    assert acct["transactions"]["T-1"]["reversed_points"] == 0
    assert acct["transactions"]["T-1"]["refunded_paise"] == 5000
    assert acct["ledger"][-1]["points_delta"] == 0


def test_malformed_and_missing_identifiers_handling():
    rules = {"points_per_100_rupees": 1}
    acct = new_account("ACCT-REG-5")

    # Missing event_id
    res1 = apply_reward_event(
        acct,
        {"type": "purchase_captured", "transaction_id": "T-1", "amount_paise": 10000},
        rules,
    )
    assert res1["points_balance"] == 0
    assert len(res1["ledger"]) == 0

    # Missing transaction_id
    res2 = apply_reward_event(
        acct,
        {"event_id": "E-1", "type": "purchase_captured", "amount_paise": 10000},
        rules,
    )
    assert res2["points_balance"] == 0

    # Non-dict inputs
    assert apply_reward_event(None, {}, rules)["points_balance"] == 0
    assert apply_reward_event(acct, None, rules)["points_balance"] == 0
    assert flag_repeat_transactions(None) == []
    assert flag_repeat_transactions("invalid") == []


def test_cap_zero_and_negative_rules_safeguards():
    assert calculate_points(100000, 1, 10, cap_points=0) == 0
    assert calculate_points(100000, 1, 10, cap_points=-10) == 0
    assert calculate_points(100000, -1, 10, cap_points=100) == 0
    assert calculate_points(100000, 1, -10, cap_points=100) == 0
    assert calculate_points(-50000, 1, 10, cap_points=100) == 0
    assert calculate_points("100000", 1, 10, cap_points=100) == 0
    assert calculate_points(100000, True, 10, cap_points=100) == 0


def test_csv_account_statement_generation():
    rules = {"points_per_100_rupees": 1}
    acct = new_account("ACCT-CSV-1")
    acct = apply_reward_event(
        acct,
        {"event_id": "P-101", "type": "purchase_captured", "transaction_id": "TX-101", "amount_paise": 200000},
        rules,
    )
    acct = apply_reward_event(
        acct,
        {"event_id": "R-101", "type": "refund_processed", "transaction_id": "TX-101", "amount_paise": 100000},
        rules,
    )

    csv_data = generate_account_statement_csv(acct)
    lines = csv_data.strip().split("\n")
    assert lines[0] == "event_id,type,points_delta,running_balance"
    assert lines[1] == "P-101,purchase_captured,20,20"
    assert lines[2] == "R-101,refund_processed,-10,10"


def test_purchase_captured_invalid_amount_safeguards():
    rules = {"points_per_100_rupees": 1}
    acct = new_account("ACCT-REG-6")

    # Boolean amount
    res_bool = apply_reward_event(
        acct,
        {"event_id": "P-B", "type": "purchase_captured", "transaction_id": "T-B", "amount_paise": True},
        rules,
    )
    assert res_bool["points_balance"] == 0
    assert "T-B" not in res_bool["transactions"]

    # Negative amount
    res_neg = apply_reward_event(
        acct,
        {"event_id": "P-N", "type": "purchase_captured", "transaction_id": "T-N", "amount_paise": -50000},
        rules,
    )
    assert res_neg["points_balance"] == 0

    # Non-dict rules
    res_rules = apply_reward_event(
        acct,
        {"event_id": "P-R", "type": "purchase_captured", "transaction_id": "T-R", "amount_paise": 100000},
        None,
    )
    assert res_rules["points_balance"] == 10


def test_repeat_transactions_and_csv_statement_edge_cases():
    # Transactions list with non-dict elements
    rows = [
        "not-a-dict",
        {"transaction_id": "1", "account_id": "A", "date": "2026-10-01", "amount_paise": 1000},
        {"transaction_id": "2", "account_id": "A", "date": "2026-10-01", "amount_paise": 1000},
        {"transaction_id": "3", "account_id": "A", "date": "2026-10-01", "amount_paise": 1000},
    ]
    # Threshold None defaults to 2
    alerts = flag_repeat_transactions(rows, threshold=None)
    assert len(alerts) == 1
    assert alerts[0]["transaction_ids"] == ["1", "2", "3"]

    # CSV Statement with empty/invalid inputs
    assert generate_account_statement_csv(None) == "event_id,type,points_delta,running_balance\n"
    assert generate_account_statement_csv({"ledger": "not-a-list"}) == "event_id,type,points_delta,running_balance\n"
    malformed_ledger_acct = {
        "ledger": [
            "not-a-dict",
            {"event_id": "E1", "type": "purchase_captured", "points_delta": True},
            {"event_id": "E2", "type": "purchase_captured", "points_delta": 5},
        ]
    }
    csv_out = generate_account_statement_csv(malformed_ledger_acct)
    assert "E1,purchase_captured,0,0" in csv_out
    assert "E2,purchase_captured,5,5" in csv_out


def test_zero_amount_purchase_refund_branch():
    rules = {"points_per_100_rupees": 1}
    acct = new_account("ACCT-ZERO")
    # 0-paise purchase is rejected by the amount <= 0 guard — same boundary as calculate_points.
    # T-0 is never recorded in transactions, so the account is unchanged.
    acct = apply_reward_event(
        acct,
        {"event_id": "P-0", "type": "purchase_captured", "transaction_id": "T-0", "amount_paise": 0},
        rules,
    )
    assert acct["points_balance"] == 0
    assert "T-0" not in acct["transactions"]
    # Any subsequent refund on T-0 is also safely rejected (unknown transaction_id).
    res = apply_reward_event(
        acct,
        {"event_id": "R-0", "type": "refund_processed", "transaction_id": "T-0", "amount_paise": 10},
        rules,
    )
    assert res["points_balance"] == 0


