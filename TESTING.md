# TESTING.md — Required submission

## Test command and environment
- **Python version:** Python 3.11+
- **Command run:** `python -m pytest -q`
- **Actual test summary:** 218 passed in 0.30s

## Edge-case evidence
| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | `amount_paise = 19999`, rate = 1 | Awards 1 point (floored) | 1 point awarded | `test_points_use_floor` |
| 2 | `cap_points = 0`, amount = 50000 | Awards 0 points | 0 points awarded | `test_cap_zero_is_respected` |
| 3 | Replay event `E1` twice | Processed once, ledger length 1 | 2 pts balance, 1 ledger item | `test_purchase_event_once` |
| 4 | Refund amount = 150000 (excess) | Ignored, balance unchanged | Refunded paise 0, balance 10 | `test_invalid_or_excess_refund_ignored` |
| 5 | Unrecognized event type `unknown` | 0 points awarded, no ledger entry | Balance 0, transactions empty | `test_unrecognized_or_declined_events_do_not_award_points` |

## Regression tests added
The following 4 regression tests were added to `tests/test_contract.py` to cover critical evaluation blind spots and safeguard bug fixes:

1. `test_multiple_partial_refunds_cumulative_reversal`: Validates incremental points deduction (-4 then -6) and ledger logging across multiple partial refunds on the same purchase.
2. `test_refund_event_replay_is_idempotent`: Proves duplicate refund event IDs are ignored and do not deduct points multiple times upon network retries.
3. `test_cumulative_refund_exceeding_purchase_ignored`: Ensures that when cumulative refunds exceed the original purchase amount, subsequent refunds are safely rejected without balance corruption.
4. `test_missing_identifiers_and_empty_inputs_handled_safely`: Verifies that empty strings, empty lists, and missing event identifiers fail safely with 0 points rather than throwing unhandled exceptions.

## Remaining failures or limitations
None. All 218 test cases pass with zero failures.