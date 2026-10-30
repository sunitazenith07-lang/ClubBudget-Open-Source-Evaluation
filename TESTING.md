# TESTING.md

## Test command and environment

- Python version: Python 3.13.15
- Command run: `python -m pytest -q`
- Actual test summary: 247 passed in 2.04s

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Invalid purchase amounts: `None`, string, float, boolean, list, dictionary | Return 0 points | Invalid inputs return 0 points | `test_invalid_purchase_amount_returns_zero` |
| 2 | Invalid points multiplier, bonus percentage, or cap | Return 0 points | Invalid rules return 0 points | `test_invalid_points_multiplier_returns_zero`, `test_invalid_bonus_returns_zero`, `test_invalid_cap_returns_zero` |
| 3 | Missing, empty, numeric, or boolean event ID or transaction ID | Do not award points or create a transaction or ledger entry | Invalid identifiers are rejected | `test_invalid_purchase_event_id_does_not_award`, `test_invalid_purchase_transaction_id_does_not_award` |
| 4 | Refund when account balance is zero but the transaction has awarded points | Balance must not become negative | Balance remains zero | `test_refund_does_not_make_balance_negative` |
| 5 | Empty input, missing transaction fields, or non-dictionary repeat records | Handle safely without exceptions or false alerts | Malformed records are ignored | `test_repeat_alert_empty_input`, `test_repeat_alert_handles_missing_fields`, `test_repeat_alert_ignores_non_dictionary_records` |

## Regression tests added

- Added tests for invalid purchase amounts, reward multipliers, bonus percentages, and caps.
- Added tests for missing or invalid event IDs and transaction IDs.
- Added a test to ensure refunds cannot make the account balance negative.
- Added tests for empty repeat-transaction input and single transactions.
- Added tests for missing fields and non-dictionary repeat-transaction records.
- Preserved the existing tests and added regression coverage in `tests/test_contract.py`.

## Remaining failures or limitations

- No failing tests remain in the final reported test run.
- The current refund implementation prevents negative balances but does not track pending reversals when awarded points have already been spent.
- The specification does not define how such pending reversals should be handled, so this requires clarification.