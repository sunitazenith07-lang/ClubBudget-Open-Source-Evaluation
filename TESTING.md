# TESTING.md — Required submission

I am a first-year student who recently finished learning the basics of Python. Below is what I tested after making the changes and how I checked the important edge cases. Every result below was actually run; I do not claim a test passed unless I ran it.

## Test command and environment
- Python version: Python 3.12.3 (verification run for this version; re-run on your own machine before submitting and update this line if it differs)
- Command run: `python -m pytest -q`, then `python -m main`
- Actual test summary: Starter: **67 failed, 147 passed (214 total)**. This version: **223 passed, 0 failed** (202 acceptance + 21 contract: 12 original + 9 new). Demo: `Points example: 27`, `Repeat warnings: []`.

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Points floor: `calculate_points(19999, 1)` | Floor: 1, not rounded to 2 | 1 | `test_points_use_floor`, `test_integer_floor_points_calculation` |
| 2 | Floor boundary: 9999 → 0, 10000 → 1 | Only complete ₹100 blocks count | 0 and 1 | `test_integer_floor_points_calculation` |
| 3 | Bonus then cap: 50000 paise, 2 pts, 50% bonus, cap 6 | Base 10 → bonus total 15 → capped to 6 | 6 | `test_bonus_then_cap` |
| 4 | Cap zero: `calculate_points(50000, 1, cap_points=0)` | 0, not "no cap" | 0 | `test_cap_zero_is_respected` |
| 5 | Invalid inputs: -10000 paise, `True` as amount, rate -1, bonus -10, cap -5 | 0 points in every case | 0 in every case | `test_negative_amount_gives_zero`, `test_boolean_and_missing_inputs_handled_safely` |
| 6 | Float/string inputs: 10000.5 paise, `"10000"`, bonus 10.5 | 0, no coercion or rounding | 0 in every case | `test_float_and_string_points_inputs_give_zero` |
| 7 | Duplicate purchase: same event E1 (25000 → 2 pts) twice | Balance stays 2, `processed_event_ids == ['E1']`, 1 ledger entry | Exactly that | `test_purchase_event_once`, `test_purchase_event_replay_is_idempotent` |
| 8 | Cumulative refunds: purchase 100000 → 10 pts; refund 30000, then 70000 | Balances 7 then 0, reversed 10, ledger `[10, -3, -7]` | Exactly that | `test_cumulative_refund_and_ledger_audit_trail` |
| 9 | Excess refund: 60000 refund, then 50000 refund on a 100000 purchase | Second refund ignored: balance 4, refunded 60000, 2 ledger entries | Exactly that | `test_multiple_partial_refunds_exceeding_purchase_ignored` |
| 10 | Invalid/excess refunds: -1, 150000, `True`, `None`, `"100"`, 1.5, `[]`, `{}` | Account unchanged: refunded 0, balance 10 | Unchanged in every case | `test_invalid_or_excess_refund_does_not_change_account` (15 cases) |
| 11 | Unknown/declined events: `purchase_declined`, `purchase_pending`, `unknown`, `""`, `None`, `1` | Balance 0, no transaction | Balance 0, no transaction | `test_unrecognized_or_declined_events_do_not_award_points`, `test_declined_event_does_not_award` |
| 12 | Repeat alert, threshold: 3 identical rows (A, D, 1000), threshold 2 | 1 alert, all 3 ids listed | 1 alert, `['0', '1', '2']` | `test_repeat_group`, `test_repeat_alert_respects_threshold` |
| 13 | Repeat alert, exactly threshold: 2 identical rows, threshold 2 | No alert (`>` not `>=`) | No alert, `[]` | `test_repeat_alert_threshold_boundaries` |
| 14 | Malformed repeat rows: rows with `account_id=None` or `transaction_id=None` | Skipped, never grouped under None | Skipped, result `[]` at threshold 1 | `test_repeat_transactions_ignore_malformed_records` |
| 15 | None / bad inputs: event `None`, rules `None` or `[]`, account `None`, list `None`, threshold `'x'` | No crash: unchanged account or `[]` | No crash: exactly that | `test_missing_identifiers_and_empty_inputs_handled_safely`, `test_none_inputs_do_not_crash_or_award`, `test_repeat_transactions_none_input_and_bad_threshold_are_safe` |
| 16 | Input not mutated: account before vs after a purchase event | Original account unchanged (deep copy) | Unchanged | `test_input_account_not_mutated`, `test_event_processing_does_not_mutate_input_account` |
| 17 | Empty input: `flag_repeat_transactions([])` | `[]` | `[]` | `test_boolean_and_missing_inputs_handled_safely` |

## Regression tests added
List the defects fixed and the tests added to prevent them from returning.
- Refund replay: `test_refund_event_replay_once`
- Cumulative refunds exceeding the purchase: `test_multiple_partial_refunds_exceeding_purchase_ignored`
- Bool and missing inputs: `test_boolean_and_missing_inputs_handled_safely`
- Missing identifiers and empty inputs: `test_missing_identifiers_and_empty_inputs_handled_safely`
- None inputs: `test_none_inputs_do_not_crash_or_award`
- Float/string inputs: `test_float_and_string_points_inputs_give_zero`
- None repeat input and bad threshold: `test_repeat_transactions_none_input_and_bad_threshold_are_safe`
- Cumulative refund and ledger audit trail: `test_cumulative_refund_and_ledger_audit_trail`
- Malformed repeat rows: `test_repeat_transactions_ignore_malformed_records`
- No existing test was deleted, edited, skipped or weakened. `tests/test_acceptance_matrix.py` and `.github/workflows/tests.yml` are unchanged.

## Remaining failures or limitations
List any known failing tests or unresolved behaviours honestly.
- Visible suite: **0 failures** on this version.
- Hidden tests are unseen and are not claimed as passed. The judgement calls most likely to differ from a hidden test are documented in `approach.md` §4 and `challenges.md` §6: float/string amounts are rejected (not coerced), and a well-formed invalid event consumes its event id.
- Not implemented: the optional stretch items (CSV statement, configurable threshold, category summary), persistence, a spend/redeem operation, and date parsing — see `optimizations.md` §5.
- Environment note: running `python -m pytest` with a Python that has no pytest installed fails before any test runs. Use a virtual environment with `pip install -r requirements-dev.txt` first, as the README instructs. Do not commit `__pycache__` or `.pytest_cache` — `.gitignore` already excludes them.
