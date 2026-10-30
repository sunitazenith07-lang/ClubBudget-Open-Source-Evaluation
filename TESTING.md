# Testing

## Environment and commands

- Python: 3.14.6
- Test command: `python -m pytest -q`
- Result: **217 passed** (0.33 seconds)
- Demo command: `python -m main`
- Demo output:
  - `Points example: 27`
  - `Repeat warnings: []`
- Static checks: Pylance reported no diagnostics for `service.py`; syntax checks passed for the changed Python files; `git diff --check` reported no whitespace errors.

The test suite was also run before the debugging fixes. That baseline was **47 failed, 167 passed**. The failures exposed missing zero-cap handling, event replay handling, and refund validation. Existing tests were not deleted, skipped, weakened, or bypassed.

## Edge-case evidence

| # | Input / scenario | Expected behaviour | Observed result | Test |
|---|---|---|---|---|
| 1 | Purchase of 9,999 paise | Integer floor rounding awards zero points | Zero points | `test_integer_floor_points_calculation` |
| 2 | 50,000 paise; 2 points per 100 rupees; 50% bonus; cap of 0 | A zero cap limits the award to zero | Zero points | `test_bonus_and_cap_matrix` |
| 3 | Replay the same captured-purchase event | Do not award points or add another processed event or ledger entry | Balance remains 2; event and ledger entry are recorded once | `test_purchase_event_replay_is_idempotent` |
| 4 | Refund with a negative, zero, non-integer, or excessive amount | Leave the refund total and balance unchanged | Invalid refunds are ignored | `test_invalid_or_excess_refund_does_not_change_account` |
| 5 | Replay the same 50,000-paise refund against a 100,000-paise purchase | Apply the refund only once | Balance is 5; refunded total is 50,000 paise; one refund ledger entry | `test_refund_event_replay_is_idempotent` |
| 6 | Refund 60,000 paise, then 50,000 paise against a 100,000-paise purchase | Reject the second refund because the cumulative total would exceed the purchase | Refunded total remains 60,000 paise; balance remains 4 | `test_refund_cannot_exceed_remaining_purchase_amount` |
| 7 | Three repeat-alert rows with a missing account ID | Do not group incomplete records into an alert | No repeat alert | `test_repeat_alert_skips_rows_missing_identifiers` |

## Regression tests added

- `test_refund_event_replay_is_idempotent` verifies that a refund event cannot be applied twice.
- `test_refund_cannot_exceed_remaining_purchase_amount` verifies cumulative refund bounds.
- `test_repeat_alert_skips_rows_missing_identifiers` verifies that incomplete transaction records do not produce repeat alerts.

## Remaining failures and submission status

- No test failures remained in the final run.
- This file documents the tests and evidence for the code changes; it does not replace the separately required `approach.md`, `challenges.md`, `optimizations.md`, and `REWARD_RULE_NOTES.md`. Those files still need to be completed before the overall submission is ready for a pull request.
