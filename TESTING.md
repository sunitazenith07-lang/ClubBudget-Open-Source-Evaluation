# Test evidence

## Test command and environment

- Python: 3.13.15
- Command: `python -m pytest -q`, run from the project directory.
- Baseline before code changes: **67 failed, 147 passed**.
- Final re-verification on 2026-10-31: **221 passed**.
- Demo command: `python -m main` — output: `Points example: 27`; `Repeat warnings: []`.

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | 9,999 paise, 1 point per 100 rupees | Floor to zero eligible hundreds; award 0 | 0 points | `test_integer_floor_points_calculation` (9,999-paise parameter) |
| 2 | 50,000 paise, 2 points per 100 rupees, 50% bonus, cap 0 | Zero cap is applied after bonus | 0 points | `test_bonus_and_cap_matrix` (50,000 / 2 / 50 / 0 parameter) |
| 3 | Replay the same 50,000-paise refund event twice on a 100,000-paise purchase | Apply the refund/reversal once | Balance 5; refunded amount 50,000; two total ledger entries (purchase and refund) | `test_refund_event_replay_is_idempotent` |
| 4 | Refund 60,000 then attempt 50,000 then refund remaining 40,000 paise on a 100,000-paise purchase | Reject the excessive second refund; allow the remaining 40,000; reverse no more than 10 points | Refunded amount 100,000; reversed points 10; balance 0 | `test_cumulative_refunds_cannot_exceed_purchase_amount` |
| 5 | Capture event without an event ID | Do not award points or create a transaction/ledger entry | Balance 0; no transaction or ledger entry | `test_missing_event_identifier_does_not_apply_purchase` |
| 6 | Repeat group includes malformed rows and duplicate transaction ID | Ignore malformed rows and avoid counting an ID twice | No alert for only one unique valid ID at threshold 2 | `test_repeat_alert_skips_malformed_rows_and_duplicate_transaction_ids` |
| 7 | One valid transaction with threshold 0 | Preserve `count > threshold` semantics and flag it | One alert | `test_zero_repeat_threshold_flags_a_single_valid_transaction` |

## Regression tests added

Added tests for invalid numeric rule/input types, refund replay, cumulative refund limits, missing event IDs, negative starting balances on purchase, malformed/duplicate repeat rows, and threshold zero.

## Remaining failures or limitations

No visible test failures remain. No pull request or CI run has been performed. The event function currently records an event ID as processed before validating event type/payload; changing that behavior requires an explicit replay policy. These notes were AI-assisted with evaluator permission, as confirmed by the requester; see [AI_USAGE.md](AI_USAGE.md).
