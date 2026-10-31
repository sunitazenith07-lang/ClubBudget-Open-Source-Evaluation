# challenges.md - COMPULSORY submission

## 1. Challenge or confusing behaviour
The hardest part was making refunds idempotent and bounded while keeping proportional reversal correct. The starter only avoided duplicate transaction creation but still appended event IDs on every replay.

## 2. Evidence
- `test_purchase_event_replay_is_idempotent` expected `processed_event_ids == [event_id]` after replay.
- `test_invalid_or_excess_refund_does_not_change_account` expected unchanged account for invalid/excess refunds.
- `test_refund_amount_bounds_and_balance` checked boundary refund amounts.

## 3. What I tried
- Ran `python -m pytest -q` to get the 45 failures.
- Traced `apply_reward_event` and compared refund calculations against expected proportional reversal.
- Tested replay manually to confirm duplicate event IDs.
- Eventually tried [successful approach]: This fixed the issue (assisted by Cline for rapid log tracing and automated test re-runs)

## 4. Resolution
- Added early idempotency return for already-processed event IDs.
- Validated refund type, positivity, original amount, and cumulative remaining balance.
- Recomputed proportional reversal using cumulative refunded paise.
- Capped reversal delta to available balance.

## 5. Proof and regression prevention
- All 214 tests pass, including replay and refund boundary tests.
- Related risk: future changes to refund cumulative logic could reintroduce over-reversal if not tested.

## 6. Unresolved challenge or next step
No code-test failures remain. Documentation and optional regression tests could be expanded, but no major blocker remains.
* Future Improvements: Given more time, I would add property-based tests (e.g., Hypothesis) to fuzz refund amounts and event IDs, plus integration tests simulating concurrent event replay. (Gemini Argon 4 and Cline were used to scaffold these test patterns).