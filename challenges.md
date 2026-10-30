# challenges.md - COMPULSORY submission

Nothing completely blocked me, but these were the parts that took the most figuring out.

## 1. Challenge or confusing behaviour
1. **The tests wouldn't run at first.** `python3 -m pytest` failed before I even touched the code.
2. **Partial refunds and rounding.** I wasn't sure whether each refund should take back its own share of points, or whether I should work it out from the total refunded so far. It turns out this matters.
3. **`True` counts as a number in Python.** The tests use `True` and `False` as refund amounts and expect them to be rejected, but `True` passes an `int` check.
4. **The dataset didn't match the rules neatly.** The rules say "process each event_id once", but 9 events in the dataset have no `event_id` at all, and 12 reuse an ID that already appeared. Some repeat groups also have amount 0.
5. **Stress testing found crashes.** After everything passed, I tried thousands of random inputs and some of them crashed the code.
6. **Ambiguity fix: two alert behaviours that were technically allowed but surprising.** In a final review against the problem statement I found that a junk threshold made alerts *more* sensitive, and that the same transaction could count as a repeat of itself.

## 2. Evidence
1. The error was `No module named pytest`, and `pip install` was refused because Homebrew Python 3.14.7 is an "externally managed environment".
2. Example: a 259900-paise purchase with 5 points per ₹100 and a 25% bonus gives 156 points. Then two refunds of 100000 and 159900 paise, which together are a full refund.
   - Doing each refund on its own: `156×100000//259900 = 60` and `156×159900//259900 = 95`, so 155 taken back. **1 point is left over after a full refund**, which is wrong.
   - Using the running total: first `156×100000//259900 = 60`, then `156×259900//259900 = 156`, so take back 156 − 60 = 96 more. **0 left**, which is correct.
3. `isinstance(True, int)` returns `True`, so a check like `amount <= 0` lets `True` through as if it were 1 paise.
4. My counting script showed that of 264 events, 9 have no `event_id`, 12 are duplicate IDs, and 152 have no `amount_paise` (only declined, pending or unknown types, which never earn anyway). 12 of the 60 repeat groups have amount 0.
5. A `transaction_id` of `[]` raised `TypeError: unhashable type: 'list'`, because Python can't use a list as a dictionary key. The same thing happened in the alert function with a list `account_id` or `date`. The random test also showed that the order of IDs in an alert changed if the input order changed.
6. Two probes:
   - `flag_repeat_transactions(rows, None)` and `flag_repeat_transactions(rows, "2")` on 2 matching rows gave 1 alert, but the default threshold gave none. A bad threshold was being turned into 1, while `repeat_threshold_from_config` turned the same bad value into 2. The two functions disagreed.
   - The same row `{'transaction_id': 'T1', ...}` sent 3 times gave an alert with `transaction_ids: ['T1', 'T1', 'T1']`. The brief is about different payments that look the same, not one row duplicated by a feed. The dataset has no duplicate IDs, so no existing test noticed.

## 3. What I tried
1. I made a virtual environment, installed the requirements into it, and ran the baseline on a clean copy of the starter code: `67 failed, 147 passed`.
2. I worked out both refund methods by hand for the example above, then ran the fixed code to check the ledger showed `balance_after` 96 and then 0.
3. I looked at which inputs were failing in `test_invalid_or_excess_refund_does_not_change_account`. The boolean ones were in there.
4. I counted the dataset fields with a small script before deciding what to do.
5. I wrote random stress tests (now in `tests/test_stress.py`) that check things that should always be true. For example: the balance is never negative, the ledger adds up to the balance, and sending the same event twice changes nothing. They also try junk values for every field.
6. For the ambiguity fix I checked which tests depend on threshold handling (`test_repeat_alert_threshold_input_is_handled`, `test_non_positive_threshold_is_treated_as_one`, the stress reference), so 0 and negatives still count as 1 and only non-integers change.
7. I also made a mistake in one of my own tests. I first wrote that `calculate_points(300000, 3, 150, 300)` should be 22, but working it out again gives 30 × 3 = 90, then 90 × 250 // 100 = 225. I fixed it before running.

## 4. Resolution
1. Used the virtual environment for everything. No project files needed changing.
2. Refund points are now worked out from the running total (`refunded_paise`), and only the difference is taken off. That way rounding can never leave points behind after a full refund.
3. Added a small `_is_int()` helper that says no to booleans, and used it for amounts, rules and the threshold.
4. Events without an `event_id` or `transaction_id` are ignored, because there's no way to tell whether they're duplicates. Amount-0 rows are left out of alerts. That's an assumption, and I wrote it down.
5. Added `_is_hashable()` so events or rows with list/dict IDs are skipped instead of crashing. Alert `transaction_ids` are now sorted. Added 13 tests for this.
6. **Ambiguity fix:** a threshold that isn't a whole number (`None`, `"2"`, `1.5`, `True`) now falls back to the default of 2, matching the config reader; 0 or negative still counts as 1. Each `transaction_id` is now counted once per group. Added 5 tests: `test_invalid_threshold_falls_back_to_default` (4 cases) and `test_same_transaction_id_is_not_counted_as_a_repeat`. All 319 tests and my 3,004-test extended stress run still pass.

## 5. Proof and regression prevention
- Tests: `test_partial_refunds_sum_to_full_reversal`, `test_cumulative_refunds_cannot_exceed_purchase`, `test_invalid_purchase_amount_creates_no_transaction[True]`, `test_event_missing_identifier_is_ignored`, `test_unhashable_identifier_is_ignored_not_crashing`, `test_alert_transaction_ids_do_not_depend_on_input_order`, `test_invalid_threshold_falls_back_to_default`, `test_same_transaction_id_is_not_counted_as_a_repeat`, `test_dataset_reward_events_keep_ledger_consistent` (all in `tests/test_regressions.py`).
- Final run: `319 passed in 0.64s` (including the 34 stress tests).
- Things that could still go wrong: an amount sent as a string like `"100000"` is rejected, not converted. So if another system sent strings, real purchases would earn nothing.

## 6. Unresolved challenge or next step
- I'm not sure whether amount-0 repeats should trigger an alert. That's really a product decision, so I'd ask. If they should, it's a one-character change (`<= 0` to `< 0`) plus updating two tests: `test_dataset_repeat_groups_are_flagged` and the reference check in `tests/test_stress.py`.
- The same review found three other ambiguous behaviours that I left as they are, because none breaks a requirement:
  - If `points_per_100_rupees` is missing from the rules, it defaults to 1 point per ₹100 (this default came with the starter code).
  - An event's `account_id` isn't checked against the account it's applied to; the caller is trusted to pass the right account.
  - A refund clamped by a low balance can take back the rest later, from points earned on another purchase. The total taken back never goes over what was awarded.
- If someone already spent their points and then gets a refund, the code only takes back what's left in the balance. A real system would need to track "points owed".
