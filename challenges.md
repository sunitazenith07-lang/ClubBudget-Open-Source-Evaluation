# challenges.md - COMPULSORY submission

## 1. Challenge or confusing behaviour
The trickiest part I worked through was handling multi-step partial refunds correctly under integer arithmetic without losing points to rounding.

If someone buys an item for 1,000 rupees (100,000 paise) and earns 10 points, and then gets three partial refunds (300 rupees, 300 rupees, and 400 rupees), calculating the points to reverse on each individual refund separately can cause truncation remainders to pile up. For example, on smaller amounts or weird point rates, rounding down three separate times can result in 1 point remaining unreversed even when 100% of the money was refunded.

Another unexpected behaviour was Python treating booleans as integers (`isinstance(True, int)` is True). Passing `amount_paise: True` passed standard integer checks and was treated as 1 paisa!

## 2. Evidence
When I ran the untouched test suite, 24 refund tests failed:
- `test_refund_amount_bounds_and_balance` failed on amounts over 100000.
- `test_invalid_or_excess_refund_does_not_change_account` failed on inputs like `True`, `False`, `-1`, and `150000`.
- `test_purchase_event_replay_is_idempotent` failed because replaying an event added duplicate ledger rows and duplicated the event ID in `processed_event_ids`.

## 3. What I tried
1. First, I tried calculating the points to reverse for each refund individually: `awarded_points * refund_amount // original_amount`. But when I tested multiple small refunds, the sum of reversed points didn't always equal the original awarded points.
2. For input validation, I initially used `isinstance(refund, int)`. This still failed `test_invalid_or_excess_refund_does_not_change_account[True]` because `True` is an instance of `int` in Python.
3. For event replay, I saw that `event_id` was being added to `processed_event_ids` regardless of whether the event was valid or a replay.

## 4. Resolution
1. **Cumulative Refund Math:** Instead of calculating reversals on each incremental refund chunk, I track the cumulative `refunded_paise` on the transaction. Then I compute the total points that *should* be reversed so far, and subtract `reversed_points` (what we already reversed):
   `cumulative_reversed = (txn['awarded_points'] * txn['refunded_paise']) // txn['amount_paise']`
   `delta = cumulative_reversed - txn['reversed_points']`
   When the refund reaches 100%, `cumulative_reversed` naturally equals `awarded_points`, so all points are guaranteed to be reversed.
2. **Boolean Check:** Added an explicit check: `not isinstance(x, bool)`.
3. **Idempotency Check:** Added a check right at the start of `apply_reward_event`:
   `if event_id in out['processed_event_ids']: return out`
   If we've seen this event before, we return the account immediately without touching the balance or ledger.
4. **Balance Safety:** Clamped the reversal delta so points balance never goes below 0.

## 5. Proof and regression prevention
- All 20 cases in `test_refund_amount_bounds_and_balance` and 15 cases in `test_invalid_or_excess_refund_does_not_change_account` now pass.
- I added a new test `test_multi_step_partial_refund` in `tests/test_regression.py` that specifically tests a 30% + 30% + 40% refund sequence on a 100,000 paise purchase and asserts that all 10 points are reversed and the ledger matches.
- Added `test_boolean_values_rejected` to verify `True` and `False` don't earn or reverse points.

## 6. Unresolved challenge or next step
The current service stores state in memory. If two refund requests for the same transaction arrived at the exact same millisecond in a multi-threaded web server, there could be a race condition when checking `txn['refunded_paise']`. In production, this would need a database row lock (`SELECT FOR UPDATE`) or a version check to make sure refunds are processed sequentially.
