# challenges.md - COMPULSORY submission

## 1. Challenge or confusing behaviour
The hardest part was the interaction between refund accounting and replay protection. The rules were not simply "add points" or "subtract points"; they required a consistent model of purchased amount, refunded amount, awarded points, and reversed points, while also rejecting duplicate events. The zero-cap case was also easy to miss because it looked like a simple bonus formula but still required an integer floor and an explicit cap of zero.

## 2. Evidence
The clearest evidence was the failing acceptance matrix: `test_bonus_and_cap_matrix` exposed the zero-cap bug, and the refund tests showed that replayed or over-limit refunds changed the balance incorrectly. For example, a purchase of 100,000 paise with a 1-point-per-₹100 rule should award 10 points. A refund of 50,000 paise should reverse exactly 5 points, while a refund of 150,000 paise should be ignored. The repeat-event tests confirmed that replaying the same event should not create extra ledger entries or points.

## 3. What I tried
I first ran the existing suite to get a factual baseline (`47 failed, 167 passed`) and then examined the exact failing assertions in `tests/test_acceptance_matrix.py` and `tests/test_contract.py`. After that, I traced the logic in `service.py` from `calculate_points()` to `apply_reward_event()` and `flag_repeat_transactions()`. I checked the smallest edge cases individually: cap zero, round-down rules, duplicate purchase IDs, partial refund proportional reversal, and refunds exceeding the original purchase total.

## 4. Resolution
The root cause was that validation was too loose and event-state mutation happened before the code proved that the event was valid. In `calculate_points()`, the function needed to enforce non-negative integer inputs and apply the cap after the bonus formula rather than treating the cap like a gentle suggestion. In `apply_reward_event()`, the code needed to reject duplicate event IDs and duplicate transaction IDs before mutating the account, and the refund branch needed to ensure `refund <= remaining_purchase_amount` before adjusting the balance. This fixed the actual cause and did not simply suppress the symptom.

## 5. Proof and regression prevention
The decisive proof was the passing final suite: `python -m pytest -q` finished with **217 passed**. The most important regression checks were the refund replay and cumulative refund tests, plus the repeat-alert safeguard for missing identifiers. The main related case that could still break is a malformed event payload with missing or non-integer identifiers; those remain intentionally rejected to protect account integrity.

## 6. Unresolved challenge or next step
There were no unresolved functional issues in the final code. The remaining work, if more time were available, would be to add a few more explicit invariant tests around ledger semantics and event ordering to document expected behaviour for future contributors.