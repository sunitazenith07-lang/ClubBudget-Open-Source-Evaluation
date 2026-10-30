# Challenges

## 1. Challenge
The trickiest behavior was splitting one purchase into several partial refunds without changing the result through rounding or allowing the cumulative refund amount to exceed the purchase.

## 2. Evidence
The baseline had **67 failing tests**. Existing refund cases showed malformed values could raise `TypeError` (for example, adding a string or list to `refunded_paise`), while negative and over-limit refunds changed the stored total. A single partial refund test did not cover cumulative rounding.

## 3. Investigation
I traced the refund update in `apply_reward_event`: the starter added the incoming amount before validating it, then computed the reversal from that mutated total. I added a regression using a 30,000-paise purchase followed by two 10,000-paise refunds and a third refund that would exceed the original amount. The first two refunds should reverse one point each cumulatively; the third must have no effect.

The system Python also rejected the requested pip install with PEP 668 (`externally-managed-environment`). I did not override that protection; I used the repository's existing git-ignored `.venv`, where the requirements were already installed, and ran the baseline there.

## 4. Resolution
The function now validates the refund as a positive, non-boolean integer and checks it against the remaining refundable amount before mutation. It calculates the target reversal from total refunded paise and awards/reverses only the difference from the amount already reversed. Duplicate event IDs return the account unchanged.

## 5. Proof
`test_multiple_partial_refunds_round_cumulatively_and_respect_original_amount` checks cumulative totals, balance, and ledger snapshots. `test_refund_replay_and_ledger_are_idempotent` checks duplicate delivery and the refund ledger entry. The final suite passed: **219 passed**.

While adding repeat-alert coverage, an initial assertion expected no alert at threshold 1 even though two distinct transaction IDs correctly exceeded it. I changed the test threshold to 2 so it specifically checks that a duplicate ID and a row missing its ID do not inflate the count.

## 6. Remaining limitations
The service operates on in-memory dictionaries and does not provide durable or concurrent idempotency; those guarantees would require a storage transaction/unique constraint. No benchmark or persistence test was performed.