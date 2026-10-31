<!-- DRAFT: resolve every [VERIFY] and [FILL] marker with your own run/edits, then delete this comment. -->
# challenges.md

## 1. Challenge or confusing behaviour
Two things were hard to reason about: (a) refund reversal rounding and what to do with an over-refund, and (b) a wrong assumption about the repeat-alert threshold that I almost acted on.

## 2. Evidence
- `isinstance(True, int)` is `True` in Python, so a refund amount of `True` passes a plain int check. The tests send `True` and `False` as refund amounts.
- The first AI suggestion was that `len(ids) > threshold` should be `>=`. The tests contradict that: `test_repeat_alert_threshold_boundaries` expects no alert at exactly `threshold` rows and one alert at `threshold + 1`.
- 259900 paise with a 10% bonus: 25 base points, then `25*110//100 = 27` (27.5 floored). The starter printed 28.

## 3. What I tried
[FILL: edit this to what you personally did. Suggested content below.]
- Grouped the 67 failures by test name; they fall into five root causes (rounding, zero cap, replay, capture consistency, refund validation).
- Read the repeat tests before changing the comparison, and found the `>` is pinned by them.
- Worked the refund maths by hand (27 points, ₹1000 of ₹2599 refunded gives 10) and compared it with the code.
- Ran every event in `records.json` through the fixed service and checked balances, the ledger and processed IDs.

## 4. Resolution
- Root cause for bool refunds: Python's bool subclasses int. Fix: `_is_int` explicitly excludes bool, so the fix is at the validation boundary and not in each test case.
- Root cause for the threshold mistake: I reasoned from one fixture instead of the tests. I kept `>` and did not change it.
- Refund policy: reject an over-refund entirely. Clamping would hide a bad event, and the tests expect no change.

## 5. Proof and regression prevention
- Tests: `test_invalid_or_excess_refund_does_not_change_account` (including `True`), `test_cumulative_over_refund_rejected_on_second_event`, `test_split_refunds_reverse_exactly_awarded`, `test_repeat_alert_threshold_boundaries`.
- Could still break: any code path that checks types with plain `isinstance(x, int)` instead of `_is_int`.

## 6. Unresolved challenge or next step
- A refund that arrives before its purchase is rejected. Because rejected events are not recorded as processed, replaying it after the purchase works, but the service does not queue it. I would test out-of-order event streams next.
- Zero-amount purchases are rejected by my assumption. I'd confirm that rule with the organiser.
- Performance is O(n²) over a stream of events (see optimizations.md).