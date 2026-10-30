# approach.md - Required submission

## 1. Baseline
- Commands run before editing: `python -m pytest -q` and `python -m main`
- Initial test result: **47 failed, 167 passed**
- Demo/output observed before the fix: the starter app printed a points value and repeated-transaction output, but the underlying rules and validation were incomplete. The failing tests showed a gap in zero-cap handling, event replay safeguards, and refund validation.

## 2. Codebase understanding
- Important files/functions inspected: `service.py`, `models.py`, `main.py`, `fixtures.py`, `tests/test_acceptance_matrix.py`, and `tests/test_contract.py`
- Rewards calculation, refund, ledger or alert flow traced: I traced the flow from `calculate_points()` through `apply_reward_event()` and into the ledger/transaction state, then verified the repeat-alert grouping path in `flag_repeat_transactions()`.
- How I confirmed my understanding: I read the contract tests and matrix tests, then validated the runtime behaviour by running the failing suite before changing code. This let me match the observed bug symptoms to the source logic instead of guessing at fixes.

## 3. Investigation and implementation strategy
- Issue 1: Zero-cap and floor-rounding behaviour was wrong. The symptom was that a valid purchase could still generate points even when the cap was zero or the rounded value should have been floor-based. The failing evidence came from `test_bonus_and_cap_matrix` and `test_integer_floor_points_calculation`. The fix was to centralise integer validation and ensure `base = (amount_paise // 10000) * points_per_100_rupees`, then apply the bonus before enforcing the cap.
- Issue 2: Event replay handling was not idempotent. The symptom was that the same `event_id` or duplicate transaction could be applied again and inflate the points balance or ledger. The evidence was the replay tests in `tests/test_acceptance_matrix.py`. The fix was to reject duplicate event IDs and duplicate transaction IDs before mutating the account, while still preserving a single ledger entry for valid events.
- Issue 3: Refund validation and proportional reversal were permissive. The symptom was that negative, zero, non-integer, or excessive refunds could still mutate `refunded_paise`, `reversed_points`, or the account balance. The relevant evidence was the refund matrix and replay tests. The fix was to require positive, valid integer amounts, enforce `refund <= remaining_purchase_amount`, and only reverse the proportional points that were actually earned.

## 4. Implementation decisions
- Main changes and why: I kept the logic in `service.py` because it contained the reward and refund rules. I added explicit guard clauses for non-negative integers and identifiers, enforced idempotent event handling, and limited refund application to the remaining purchase amount before calculating the proportional reverse.
- Alternatives considered and why rejected: I considered adding ad hoc checks in the tests only, but that would hide the root cause instead of fixing the logic. I also considered broad refactors, but the bug pattern was local and the simplest clear guard-based fix preserved the existing API and behaviour.
- Assumptions: the rules are intentionally conservative: invalid amounts produce zero points, duplicate events are ignored, and refunds can only reduce the balance by the portion of the original purchase that has not already been refunded.

## 5. Verification
- Tests added or changed: I validated the existing matrix and added regression checks covering refund replay, refund bounds, and missing identifier handling in the repeat-alert path (`test_refund_event_replay_is_idempotent`, `test_refund_cannot_exceed_remaining_purchase_amount`, and `test_repeat_alert_skips_rows_missing_identifiers`).
- Commands run and actual results: `python -m pytest -q` -> **217 passed in 0.16s**. `python -m main` -> `Points example: 27` and `Repeat warnings: []`.
- Edge cases verified: zero-cap purchases, floor rounding, inactive duplicate events, negative/excess refunds, partial refund reversal, and repeat-alert records missing account IDs or dates.
- Remaining failures or known limitations: none in the final suite. The rules remain intentionally strict and are documented in the notes files; no additional unresolved defects were observed during validation.