# approach.md - Required submission

# 1. Baseline

Before touching any code, I installed the dependencies with python -m pip install -r requirements-dev.txt. That pulled in pytest 9.2.0, colorama, iniconfig, packaging, pluggy and pygments. Then I ran python -m pytest -q.

The first run gave 147 passed and 67 failed in 1.72s.

I also ran python main.py. It ran fine, but the points it printed were wrong. The cause was a rounding bug: the code used round() where it should have used floor division.

# 2. Understanding the codebase

I started with service.py, mainly calculate_points(), apply_reward_event() and flag_repeat_transactions(). I also read new_account() in models.py to see how the account state dictionary gets built. For expected behaviour, I went through tests/test_acceptance_matrix.py and tests/test_contract.py.

Here is how the main flows work:

calculate_points takes the base points as amount // 10000 * rate, applies any bonus percentage, then caps the result if a cap is given.

apply_reward_event handles two event types. A purchase_captured event records the transaction and awards points. A refund_processed event reverses points in proportion to the refund. Every processed event_id is added to processed_event_ids.

flag_repeat_transactions groups transactions by (account_id, date, amount_paise) and flags any group that goes over the threshold.

To check I’d understood all this, I ran individual tests, read the assertion failures, and walked through service.py by hand against requirements 1 to 8 in STUDENT_PROBLEM_STATEMENT.md.

# 3. Finding and fixing the defects

I found four defects. For each one I’ll cover what failed, why, and what I did about it.

Issue 1: round() instead of floor division.
test_points_use_floor failed because calculate_points(19999, 1) returned 2 instead of 1. test_capture_purchase_records_consistent_transaction also failed for 19999, with assert 1 == (19999 // 10000).

My guess was that round(19999 / 10000) works out to round(1.9999), which is 2. Requirement 1 says the base should be floor(amount_paise / 10000) * points_per_100_rupees, so that confirmed it. I swapped in amount_paise // 10000 and added an early return of 0 for negative amounts.

Issue 2: cap_points=0 was ignored.
test_cap_zero_is_respected failed. calculate_points(50000, 1, cap_points=0) gave 5 instead of 0. The (50000, 2, 50, 0, 0) case in test_bonus_and_cap_matrix failed too.

The code used if cap_points:, and Python treats 0 as false. So with a cap of zero, the min(points, cap) line never ran. I changed the check to if cap_points is not None:.

Issue 3: no idempotency on events.
test_purchase_event_replay_is_idempotent failed. processed_event_ids held ['PURCHASE-001', 'PURCHASE-001'] when it should have held one entry. test_purchase_event_once failed as well.

The cause was that out['processed_event_ids'].append(event_id) ran every time, with no check for whether the event had been seen. Requirement 4 says each event_id is processed once, so a replay can’t change balances twice. I added if event_id in out['processed_event_ids']: return out at the top of apply_reward_event.

Issue 4: refunds weren’t validated.
test_refund_amount_bounds_and_balance and test_invalid_or_excess_refund_does_not_change_account failed. The inputs included negatives, oversized amounts, booleans, None, strings, floats, lists and dicts.

The code ran txn['refunded_paise'] += refund with no checks, so bad input could corrupt the balances. Requirement 5 says never to reverse more than was awarded or allow a negative balance. Requirement 8 asks for safe handling of boundary values. I added this guard:

```python
if not isinstance(refund, int) or isinstance(refund, bool) or refund <= 0 or refund > txn['amount_paise']:
    return out
```
# 4. Decisions and trade-offs

I used // over round() because the spec calls for integer reward math, and floor division matches it exactly.

The is not None check means a cap of zero really does cap points at zero.

I put the idempotency check first so a replayed event can’t change anything, including the ledger.

The refund checks are strict on purpose. Floats, booleans, non-positive amounts and oversized requests are all ignored, and the account stays as it was.

I looked at two other approaches and dropped them. The first was removing duplicate event IDs after processing. That fails because the event would already have changed balances and ledger entries by then. The second was clamping bad refunds down to the maximum allowed. The contract tests want the account returned unchanged, with refunded_paise == 0, so clamping would break them.

I made a few assumptions. event_id is always a valid, hashable string. A refund amount has to be a real int, and since bool is a subclass of int in Python, booleans need filtering out explicitly. Point balances can’t go below zero, which I enforce with max(0, points) and by limiting refund deductions.

# 5. Verification

I didn’t change any test files. Everything in tests/test_acceptance_matrix.py and tests/test_contract.py is as I found it.

After the fixes, python -m pytest -q gave 214 passed and 0 failed in 0.45s. python main.py printed a points example of 27 and repeat warnings of [].

I also checked these edge cases:

An amount_paise of 19999 now floors to 1 point, not 2.

A cap_points of 0 gives 0 points.

A replayed event_id is ignored, with no duplicate tracking and no double points.

Invalid refunds (negative, zero, bool, None, string, float, list, dict) leave the account untouched with refunded_paise == 0. So does a refund larger than the purchase.

I know of no remaining issues. All 214 tests pass.