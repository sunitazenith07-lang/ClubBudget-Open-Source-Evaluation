# Testing

## Test command and environment
- Python: 3.14.7; pytest: 9.2.0.
- Installed dependencies with `& .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt` in the ignored project virtual environment.
- Baseline `& .\.venv\Scripts\python.exe -m pytest -q`: **67 failed, 147 passed** (214 total).
- Final `& .\.venv\Scripts\python.exe -m pytest -q`: **219 passed**.
- Final `& .\.venv\Scripts\python.exe -m main`: `Points example: 27`; `Repeat warnings: []`.

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Amount `19999` paise, 1 point per 100 rupees | Floor to 1 base point | Returned 1 point | `test_integer_floor_points_calculation` |
| 2 | Amount `50000`, cap `0` | Cap is applied; award 0 | Returned 0 points | `test_cap_zero_is_respected` |
| 3 | Boolean points rule or fractional bonus | Reject malformed rule; award 0 | Returned 0 points | `test_invalid_rule_types_do_not_generate_points` |
| 4 | Replay refund `R` for 25,000 paise against a 100,000-paise purchase | Do not apply twice; reverse 2 points total | Balance stayed 8; refund total stayed 25,000; ledger had one purchase and one refund entry | `test_refund_replay_and_ledger_are_idempotent` |
| 5 | Refund a 30,000-paise purchase in two 10,000-paise portions, then attempt 10,001 more | Cumulative floor reversal is 2 points; reject amount exceeding remaining purchase value | Refunded total stayed 20,000; balance stayed 1 | `test_multiple_partial_refunds_round_cumulatively_and_respect_original_amount` |
| 6 | Repeat rows include duplicate `T1` and a missing transaction ID; threshold 2 | Count only unique valid transaction IDs; do not alert | Returned no alert | `test_repeat_alert_skips_missing_and_duplicate_transaction_ids` |

## Regression tests added
Added coverage for invalid rule types, missing event IDs, refund replay and ledger fields, cumulative partial refunds and over-refund, and repeat-row identifier validation. Existing tests were preserved.

## Remaining failures or limitations
No known test failures. State is in memory only; durable/concurrent idempotency is outside this implementation. No performance benchmark was run.