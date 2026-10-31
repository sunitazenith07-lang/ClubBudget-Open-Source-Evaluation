<!-- DRAFT: resolve every [VERIFY] and [FILL] marker with your own run/edits, then delete this comment. -->
# TESTING.md

## Test command and environment
- Python version: [FILL: output of `python --version`]
- Command run: `python -m pytest -q`
- Actual test summary: [VERIFY] 226 passed (214 provided tests + 12 regression tests). Before the fixes: 67 failed, 147 passed.

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | 9999 paise, rate 1 | 0 points (floor) | 0 | `test_integer_floor_points_calculation[9999-0_0]` |
| 2 | `cap_points=0`, 50000 paise | 0 points | 0 | `test_cap_zero_is_respected` |
| 3 | Refund amount `True` / `False` / `"100"` / `1.5` | Ignored, balance unchanged | Ignored | `test_invalid_or_excess_refund_does_not_change_account` |
| 4 | Same `event_id` replayed | Balance changes once, one ledger entry | Once | `test_purchase_event_replay_is_idempotent` |
| 5 | Purchase with no / empty / non-string `event_id` | Rejected, nothing recorded | Rejected | `test_missing_event_id_is_rejected_and_not_recorded` |
| 6 | Two refunds of 60000 on a 100000 purchase | Second rejected, state unchanged | Rejected | `test_cumulative_over_refund_rejected_on_second_event` |
| 7 | 259900 purchase, refunds 100000 then 159900 | Balance 17, then 0; reversed = awarded | 17, then 0 | `test_split_refunds_reverse_exactly_awarded` |
| 8 | Three repeat rows with `account_id=None` | No alert | No alert | `test_incomplete_records_do_not_form_repeat_group` |

## Regression tests added
Defects fixed (see approach.md) and the tests added in `tests/test_regressions.py`:
- Bool amounts and rules: `test_bool_amount_and_rules_give_zero`
- Floor and bonus on the demo input: `test_demo_example_floors_bonus_to_27`
- Missing IDs (3 parameter cases): `test_missing_event_id_is_rejected_and_not_recorded`
- Duplicate capture under a new event ID: `test_duplicate_capture_with_new_event_id_awards_once`
- Over-refund and split refunds: `test_cumulative_over_refund_rejected_on_second_event`, `test_split_refunds_reverse_exactly_awarded`
- Zero-delta refund is still ledgered: `test_tiny_refund_reverses_zero_but_is_ledgered`
- Refund replay: `test_refund_replay_is_idempotent`
- Ledger integrity: `test_ledger_sums_to_balance`
- Incomplete alert records: `test_incomplete_records_do_not_form_repeat_group`

## Remaining failures or limitations
- No failing tests in my run [VERIFY].
- The CI result on my PR: [FILL after pushing].
- Out-of-order events (refund before purchase) are rejected rather than queued. Zero-amount purchases are rejected by assumption.