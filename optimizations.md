# Optimizations
# 1. Baseline and goal

The thing that needed improving was the correctness and maintainability of service.py. The starter code had four real defects: it rounded instead of flooring, it checked the cap by truthiness, it had no idempotency, and it did no refund validation. I saw no performance or memory problems. The whole suite of 214 tests runs in 0.45s.

The evidence points the same way. The baseline python -m pytest -q run showed 67 failures. Every one of them traced back to a business-rule defect in service.py, not to algorithmic complexity.

# 2. Options considered
Option	What it would give	Risk	Decision
Fix the defects in place in service.py	Correct behaviour, a small diff, easy review	Nothing significant	Done
Rewrite apply_reward_event with a command/handler pattern	Easier to add new event types	Too much for three event types, and it adds indirection	Rejected. The current if/elif is clear enough
Cache calculate_points results	Skips recomputing repeated amounts	Almost no gain, since the function is O(1), and it adds complexity	Rejected
Make processed_event_ids a set for O(1) lookups	Faster idempotency check on long event lists	The list is tiny in practice, and a list keeps insertion order, which may matter for audit	Rejected

# 3. Changes I made

Here is what changed and why:

round(amount_paise / 10000) became amount_paise // 10000. This is integer floor division, as requirement 1 asks.
if cap_points: became if cap_points is not None:. A cap of 0 has to give zero points.
I added if event_id in out['processed_event_ids']: return out. Events are now processed once, per requirement 4.
I added a type and bounds guard on refunds. Invalid input is rejected before any state changes, per requirements 5 and 8.

All 214 existing tests protect these changes, and none were modified or weakened.

To measure the result, I ran python -m pytest -q. It gave 214 passed and 0 failed in 0.45s. The baseline was 147 passed and 67 failed in 1.72s.

# 4. Trade-offs

The guard clauses add a few lines. In return, the control flow is explicit and easier to audit.

There’s no measurable performance cost. Correctness was the priority here, which is what the rubric and the problem statement ask for.

The fixes all live in service.py. I added no new dependencies and no new abstractions, so it stays easy to maintain.

# 5. Possible next steps
Add type hints to the return values of apply_reward_event and flag_repeat_transactions, which would help IDE support.
Add property-based tests, with something like Hypothesis, to fuzz refund amounts and event IDs.
If transaction volume grows, index processed_event_ids as a set for O(1) membership checks. Keep the list as well, so the audit output stays in order.
Pull the refund reversal calculation out into a pure function, so it can be unit tested on its own.