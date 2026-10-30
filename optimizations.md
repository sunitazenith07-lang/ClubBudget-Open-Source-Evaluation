# optimizations.md - Required submission

No performance optimization was implemented or measured. The changes were for correctness and clarity. The test suite runs in about 0.06 s (264 tests), so speed was not the problem.

## 1. Baseline and objective
- What needed improvement: correctness first (67 failing tests), then readability. The starter put each function on a few long lines separated by `;`, which made the refund bug hard to see.
- Evidence: the failures pointed to three things — float rounding, missing validation, and no duplicate check. None of them were performance problems.

## 2. Options considered
| Option | Expected benefit | Risk | Decision |
|---|---|---|---|
| Integer floor (`//`) instead of `round(a / 10000)` | Exact results, no float error | None | **Done** |
| One `_is_int` validation helper | Same rules everywhere, `bool` rejected once | A small extra function | **Done** |
| Recompute refund reversal from the cumulative total | No leftover points from rounding | Needs `refunded_paise` stored per transaction (already in the model) | **Done** |
| Keep `processed_event_ids` as a `list` | Matches the existing model and tests (`== ['E1']`) | O(n) duplicate check per event | **Kept** |
| Change it to a `set` | O(1) duplicate check | Breaks the account shape the tests compare against; loses event order | Rejected |
| Keep a private `set` alongside the list | O(1) check, list unchanged | Two copies that can drift apart; the account is deep-copied on every call anyway | Rejected for now |
| Avoid `deepcopy` on every event | Less copying per event | Tests require the input account is not mutated; manual copying is easy to get wrong | Rejected |

## 3. Changes implemented
- Change and reason: integer-only points maths; a `_is_int` helper; early `return out` for rejected events so each rule is one readable check; cumulative refund reversal; a named constant `PAISE_PER_100_RUPEES` instead of `10000`; a `_ledger_entry` helper so every ledger row has the same fields.
- Tests that protect correctness: all 214 original tests plus 35 in `tests/test_regressions.py`, including two that replay all of `data/records.json`.
- Measurement method and result: not measured. I don't claim any speed change.

## 4. Trade-offs
- **Readability vs brevity:** `service.py` grew from 37 to about 90 lines, but each rule is now one visible line that can be pointed to in a walkthrough.
- **Correctness vs speed:** `deepcopy` and the list lookup are O(size of account history) per event. That is fine for this offline service and the tests, but would not be for an account with millions of events.
- **Strict vs lenient input:** rejecting strings such as `"100000"` is safer for money, but less forgiving if an upstream system sends strings.

## 5. Further improvements
- If accounts get large: store processed IDs in a set (or a database unique index) and stop deep-copying the whole history. Validate by timing `apply_reward_event` on accounts with 10k / 100k events before and after, and re-run the full test suite.
- ~~Make the repeat threshold configurable~~ — done as the stretch item: `repeat_threshold_from_config()` and `python -m main --threshold N`.
- Replace the plain dicts with dataclasses so a typo in a field name fails loudly.
