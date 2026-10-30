# optimizations.md - Required submission

I am a first-year student who recently finished learning the basics of Python. While fixing the project, I also looked at whether the code could be made easier to read and whether some unnecessary work could be avoided. I claim no speedup in this file, because I did not measure one.

## 1. Baseline and objective
- What needed improvement (correctness, clarity, complexity, memory, repeated work, maintainability)? Correctness first, then clarity and input checking. Speed was not the main objective: the dataset is small (40 accounts, 180 repeat records, 264 event examples), and the whole test suite runs in about 0.2 seconds.
- What evidence suggested an improvement could help? The starter test run had 67 failing tests out of 214. Most problems were missing input validation, the points rounding logic, and duplicate event handling. The starter also used floating-point division with `round(amount_paise / 10000)`, which gave wrong points for some amounts (19999 paise gave 2 instead of 1, demo gave 28 instead of 27).

## 2. Options considered
Describe each option's expected benefit and risk, including rejected ideas.
- Option 1 (chosen): Keep `deepcopy(account)`, add early checks for invalid and duplicate events, use integer division `//`, and use one shared `is_valid_int` helper. Benefit: the original account is never changed accidentally, and the same validation rule cannot be forgotten in one place. Risk: `deepcopy` copies the whole account every time, which could use more memory for very large accounts — not measurable at this scale.
- Option 2 (rejected for now): Avoid `deepcopy` and copy only the parts that change. Benefit: faster and less memory for large accounts. Risk: if I forgot to copy one nested dictionary or list, the original account could be changed by accident, and the mutation tests would fail.
- Option 3 (rejected): Use a `set` for `processed_event_ids`. Benefit: O(1) membership checking. Risk: tests expect a list in insertion order (`['E1']`), and per-account event counts are small.
- Option 4 (rejected): Use `math.floor` with float division. Benefit: also gives a floor. Risk: float division can lose precision on very large integers; integer `//` is exact and simpler.

## 3. Changes implemented
- Change and reason: Integer arithmetic throughout `calculate_points` — correctness. One `is_valid_int` helper — readability and consistency. Early-return guards for missing and duplicate events, and for `None` / unusable inputs — robustness.
- Tests that protect correctness: the full floor/bonus/cap parametrised matrix, `test_boolean_and_missing_inputs_handled_safely`, `test_float_and_string_points_inputs_give_zero`, `test_invalid_or_excess_refund_does_not_change_account` (including `True` as a refund), and the final tests for missing identifiers, `None` inputs, and bad thresholds.
- Measurement method and result (only if measured): No speedup is claimed. The suite time (about 0.2 seconds for 223 tests) is reported as a run time, not as an improvement. Before, `None` inputs raised `AttributeError` or `TypeError`; after, they return an unchanged account or `[]`. That is a behaviour change, not a performance measurement.

## 4. Trade-offs
Explain trade-offs involving clarity, correctness, performance, memory, or maintainability.
- Correctness over cleverness: integer arithmetic and an explicit `is not None` cap check are slightly more verbose than `round()` and `if cap_points:`, but they say exactly what the problem statement says.
- Clarity over micro-performance: the helper function and the spelled-out refund formula (total reversed, then delta) cost a few lines, and they make the ledger invariant auditable: the sum of ledger deltas equals the balance. I checked that by hand on a multi-transaction account: purchases 100000 + 50000, refund 40000 on the first → balance 11, ledger sum 11.
- Safety over strictness: invalid inputs return 0 or a no-op instead of raising an exception. Trade-off: a caller bug (for example passing a string amount) is silently ignored rather than loudly failing. That trade-off is forced by the problem statement ("handle safely") and by the visible tests, which expect no-op behaviour — but in a production service I would log rejected events instead of dropping them silently. There is currently no logging in this codebase.
- Compatibility over ideal design: `processed_event_ids` stays a list, repeat sorting stays by `str(key)`, and well-formed invalid events still consume their event id — all to preserve starter and test-visible behaviour (see `challenges.md` §6).

## 5. Further improvements
What would you do next with more time, and how would you validate it?
1. Rejected-event distinction: record rejected event ids separately, so a corrected retry can be accepted while true replays stay blocked. Validate with a test: declined `E1`, then purchase `E1` succeeds, then purchase `E1` again is blocked.
2. Logging of rejected inputs: log (not raise) invalid amounts, excess refunds and malformed repeat rows, so silent no-ops become auditable. Validate by checking the log, not by changing any balance.
3. Repeat-group deduplication decision: decide, with the problem setter, whether the same transaction id appearing twice in the input should count once. Validate against the dataset's deliberate repeat groups in `data/records.json`.
4. One stretch feature only: the configurable repeat threshold is the smallest and most testable stretch item; a CSV account statement would come second. Either would need its own tests and a note in `TESTING.md`, and neither should be started until the required behaviour is green, which it now is.
5. Date handling, only if the specification ever requires it: parse `date` values instead of comparing plain strings, so `2026-10-21` and `2026-10-21T00:00:00` are not treated as different days. No evidence in the current data suggests this is needed, so it is deliberately not implemented.
