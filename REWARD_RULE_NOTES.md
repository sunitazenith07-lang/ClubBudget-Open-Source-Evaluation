# REWARD_RULE_NOTES.md — Required submission

Complete this file with your own actual examples and results. Do not leave prompts unanswered.

## 1. Worked points calculation
Show one purchase calculation from amount in paise through base points, bonus and cap. State the rounding rule at each step and include the actual output.

## 2. Partial-refund example
Show the points originally awarded, the refund amount, how the reversal is calculated, the resulting balance, and the relevant ledger entry.

## 3. Three edge cases
For each, provide input, expected behaviour, actual observed result, and the test that verifies it.
1. Duplicate events, Ignored properly now, Stops double points.
2.Over-refunding, Blocked by validation, Prevents negative balances.
3.Zero cap, Handled with None, Fixed cap bug.

## 4. Assumptions and limitations
Rounding Assumptions: Uses floor division to award points only for complete ₹100 blocks, avoiding premature rounding inflation.

Missing-Field Handling: Uses .get() defaults and explicit checks (not event_id, not txn_id) to drop incomplete requests.

Repeat-Alert Threshold: Defaults to threshold = 2, flagging groups with strictly more than 2 identical transactions.

Unresolved Issues: None critical; prior starter defects (idempotency, over-refunds, zero caps, and boolean injections) are fully resolved.