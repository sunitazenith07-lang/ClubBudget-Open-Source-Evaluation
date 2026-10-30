# challenges.md - COMPULSORY submission

There was no single blocker that stopped progress. The real difficulties were an environment problem, two places where the requirements were ambiguous against the dataset, a Python type trap, and one mistake in my own test that was caught before running.

## 1. Challenge or confusing behaviour
1. **Tests would not run at first.** `python3 -m pytest` failed before any code was involved.
2. **Partial refunds and rounding.** It was unclear whether each refund should reverse `floor(awarded × refund / amount)` on its own, or whether the reversal should be recomputed from the cumulative refunded amount.
3. **`True` is a valid integer in Python.** `test_invalid_or_excess_refund_does_not_change_account` includes `True` and `False` as refund amounts and expects them rejected.
4. **Dataset events without IDs, and zero-amount repeat groups.** The requirement says "process each event_id once", but most dataset events have no `event_id`. The repeat note says every three records form a group, but some groups have amount 0.
5. **A wrong expected value in my own regression test.**

## 2. Evidence
1. `No module named pytest` from Homebrew Python 3.14.7; a plain `pip install` is refused on this Python (externally managed environment).
2. Purchase of 259900 paise at 5 points/₹100, 25% bonus → 156 points. Refunds of 100000 then 159900 paise (a full refund in total):
   - per-refund flooring: `156×100000//259900 = 60`, `156×159900//259900 = 95` → 155 reversed, **1 point left after a full refund**.
   - cumulative: `156×100000//259900 = 60`, then `156×259900//259900 = 156` → 96 more, **0 left**.
3. `isinstance(True, int)` is `True`, so `amount <= 0` alone lets `True` through as 1 paise.
4. Profiling `data/records.json`: 157 of 264 reward events have no `event_id`; 180 repeat records form 60 groups of 3, of which 12 have `amount_paise == 0` (48 groups have a positive amount).
5. `test_bonus_over_100_percent_then_cap` first asserted `calculate_points(300000, 3, 150, 300) == 22`. Recomputing by hand: 300000 // 10000 = 30, × 3 = 90, × 250 // 100 = 225.

## 3. What I tried
1. Created a virtual environment, installed `requirements-dev.txt` into it, and ran the baseline on a clean export of the starter commit (`git archive HEAD`) so the result could not include my edits. Baseline: `67 failed, 147 passed`.
2. Wrote out both refund formulas for the 259900-paise example and ran the fixed code to confirm the output (`balance_after` 96, then 0).
3. Grouped baseline failures by test function to find which inputs failed; the 13 failures in `test_invalid_or_excess_refund_does_not_change_account` included the boolean and non-integer cases.
4. Counted dataset fields and groups with a short script before deciding how to handle them.
5. Re-checked every expected value in the new test file by hand before the first run.

## 4. Resolution
1. Documented the venv setup in `approach.md`; no project files needed changing.
2. Reversal is recomputed from cumulative `refunded_paise` and only the difference is applied, so rounding never leaves points behind after a full refund. This fixes the cause (accumulated floor error), not one example.
3. Added `_is_int()`, which rejects `bool`, and used it for amounts, rule values and the threshold.
4. Events missing `event_id` or `transaction_id` are ignored, because without an ID they cannot be de-duplicated. Zero/negative amounts are excluded from repeat alerts because they are not real purchases; this gives 48 alert groups on the dataset and is listed as an assumption.
5. Corrected the expected value to 225 before running; the test then passed.

## 5. Proof and regression prevention
- `tests/test_regressions.py::test_partial_refunds_sum_to_full_reversal`, `test_cumulative_refunds_cannot_exceed_purchase`, `test_invalid_purchase_amount_creates_no_transaction[True]`, `test_event_missing_identifier_is_ignored`, `test_dataset_repeat_groups_are_flagged`, `test_dataset_reward_events_keep_ledger_consistent`.
- Final run: `249 passed in 0.06s` after the core fix, `264 passed in 0.06s` after adding the configurable threshold, `277 passed in 0.07s` after the stress-test fixes.
- Could still break: an amount passed as a numeric string such as `"100000"` is rejected rather than parsed; if upstream systems send strings, real purchases would earn nothing.

## 6. Unresolved challenge or next step
- Whether zero-amount repeats should alert is a product decision; I would confirm with the organiser and, if needed, change `key[2] <= 0` to `key[2] < 0` and update `test_dataset_repeat_groups_are_flagged`.
- Points spent elsewhere are not modelled; the reversal is clamped to the current balance, so a refund after redemption reverses fewer points than it should. A real system would need a separate "points owed" record.
