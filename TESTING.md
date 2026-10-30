# TESTING.md — Required submission

Complete this file with test evidence from your own work. Include at least five edge cases. Do not claim a test passed unless you ran it.

## Test command and environment
- **Python version:** Python 3.15.0 (macOS Darwin arm64)
- **Command run:** `python -m pytest -q`
- **Actual test summary:** `224 passed in 0.06s` (all 214 visible contract/acceptance tests + 10 comprehensive regression tests passed)


## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Amount immediately below 200 rupees: `amount_paise = 19999`, `points_per_100_rupees = 1` | Floor arithmetic calculates `19999 // 10000 * 1 = 1` point. Must not round up to 2. | `1` | `tests/test_contract.py::test_points_use_floor` & `test_acceptance_matrix.py::test_integer_floor_points_calculation[19999-1]` |
| 2 | Zero cap value: `amount_paise = 50000`, `points_per_100_rupees = 1`, `cap_points = 0` | Zero cap must be respected, awarding exactly 0 points. Must not be bypassed due to truthiness evaluation. | `0` | `tests/test_contract.py::test_cap_zero_is_respected` & `test_acceptance_matrix.py::test_bonus_and_cap_matrix[50000-2-50-0-0]` |
| 3 | Replay of purchase event: Same `event_id = "E1"` submitted twice with `amount_paise = 25000` | Replayed event is recognized as duplicate; balance is credited once only and `processed_event_ids` contains single entry. | `points_balance = 2`, `processed_event_ids = ['E1']`, `len(ledger) = 1` | `tests/test_contract.py::test_purchase_event_once` & `test_acceptance_matrix.py::test_purchase_event_replay_is_idempotent[PURCHASE-000]` |
| 4 | Boolean / non-numeric refund payload: `type = "refund_processed"`, `amount_paise = True` or `"100"` | Malformed type is rejected without mutation; balance remains intact and no refund is credited. | `refunded_paise = 0`, `points_balance = 10` | `tests/test_acceptance_matrix.py::test_invalid_or_excess_refund_does_not_change_account[True]` |
| 5 | Over-refund attempt: Purchase of `100000` paise followed by refund of `150000` paise | Over-refund is rejected; transaction state and account balance remain unchanged. | `refunded_paise = 0`, `points_balance = 10` | `tests/test_contract.py::test_invalid_or_excess_refund_ignored` & `test_acceptance_matrix.py::test_refund_amount_bounds_and_balance[150000]` |
| 6 | Multi-step sequential partial refunds: Purchase `100000` paise (10 pts), Refund 1 `30000` paise, Refund 2 `70000` paise | Proportional integer reversals: 3 pts reversed on first refund, 7 pts on second; final balance 0; third refund rejected. | `reversed_points = 10`, `points_balance = 0`, `refunded_paise = 100000` | `tests/test_regression.py::test_cumulative_partial_refunds_and_over_refund_rejection` |
| 7 | Non-captured purchase events: Event with `type = "purchase_declined"` or `type = "purchase_pending"` | Only `purchase_captured` events may earn points; declined/pending events award 0 points and create no transactions. | `points_balance = 0`, `transactions = {}` | `tests/test_contract.py::test_declined_event_does_not_award` & `test_acceptance_matrix.py::test_unrecognized_or_declined_events_do_not_award_points[purchase_declined]` |

## Regression tests added
The following defects were resolved and backed by automated regression tests in `tests/test_regression.py`:
1. **Refund Event Replay Idempotency:** Added `test_refund_event_replay_is_idempotent` ensuring replaying a `refund_processed` event does not deduct points a second time or duplicate ledger entries.
2. **Cumulative Partial Refunds and Over-Refund Guard:** Added `test_cumulative_partial_refunds_and_over_refund_rejection` verifying exact cumulative reversal across split refunds and rejection of subsequent over-refunds.
3. **Sequential Truncation Precision:** Added `test_proportional_integer_truncation_across_multiple_refunds` verifying exact integer reversal tracking over multiple partial refunds.
4. **Sub-100-Rupee Purchase Refund:** Added `test_zero_awarded_purchase_refund_safety` ensuring that refunding a transaction that originally earned 0 points does not reverse negative points or corrupt ledger balance.
5. **Missing Identifiers & Non-Dict Input:** Added `test_malformed_and_missing_identifiers_handling` confirming that events missing `event_id` or `transaction_id` are safely ignored.
6. **Negative Rules and Cap Boundary Safeguards:** Added `test_cap_zero_and_negative_rules_safeguards` verifying zero/negative caps, negative bonus percentages, and non-integer types generate zero points safely.
7. **CSV Statement Generation (Stretch Work):** Added `test_csv_account_statement_generation` verifying header and running balance computation.

## Remaining failures or limitations
- There are **zero** remaining test failures across the entire suite. All 214 baseline tests and 10 new regression tests pass cleanly (224 total).
- *Known Limitation:* The current offline implementation operates entirely in memory. For a concurrent multi-threaded environment, distributed locking or transactional database isolation would be necessary to avoid race conditions on high-frequency concurrent refunds for the same account.

