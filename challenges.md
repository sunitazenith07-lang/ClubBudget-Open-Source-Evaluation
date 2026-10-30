# challenges.md - COMPULSORY submission

I did not encounter a major blocker in the final stage, but there were a few subtle contract details that required careful debugging. The hardest edge case was refund logic combined with idempotent event handling, because both rules affect the same account balance and the same transaction record.

## 1. Challenge or confusing behaviour
The most confusing behaviour was the refund path. The contract says:
- refunds should reverse points proportionally
- refunds must never exceed the original purchase amount
- negative or malformed amounts must be ignored
- duplicate event IDs must not alter the account twice

The starter implementation violated several of these rules at once. It used blind refund accumulation, did not validate bounds, and appended every event ID to the processed list without an idempotency guard.

## 2. Evidence
The evidence came from the failing acceptance tests, especially the refund and replay cases.

Examples:
- `test_refund_amount_bounds_and_balance[125000]` failed because the code treated an over-refund as valid and set `refunded_paise` to `100000` instead of `0`.
- `test_invalid_or_excess_refund_does_not_change_account[100001]` failed because invalid refund amounts were still accepted.
- `test_purchase_event_replay_is_idempotent` failed because the same event could be processed more than once and double-award points.

The actual root cause was not just bad arithmetic; it was a missing validation layer around event semantics.

## 3. What I tried
I first reproduced the failures with the repository test suite:
- `python3 -m pytest -q`
- This showed the failing refund and replay assertions.

Then I traced the data flow in `service.py`:
- `calculate_points()` was using rounding instead of floor division.
- `apply_reward_event()` processed every refund without checking `amount_paise` bounds.
- `processed_event_ids` was updated unconditionally, so replayed event IDs were not blocked.
- `flag_repeat_transactions()` was grouping records too broadly and did not filter invalid rows.

I tested each hypothesis by checking the rule contract against the failing assertions and then adjusting the implementation in one focused pass.

## 4. Resolution
The root cause was the missing guard conditions and wrong arithmetic operation. I changed the logic to:
- use integer floor division (`//`) for all point calculations
- reject negative, boolean, and malformed values early
- block duplicate `event_id`s before processing
- cap refund amounts to the remaining refundable amount
- reverse points proportionally without allowing the balance to go below zero
- ignore invalid repeat-alert rows before grouping

This fixed the cause, not just the symptom, because it enforced the business contract at the point where the state changes.

## 5. Proof and regression prevention
The fix is demonstrated by the passing suite:
- `python3 -m pytest -q`
- Result: `214 passed in 0.04s`

Relevant protections include:
- reward arithmetic tests in `tests/test_acceptance_matrix.py`
- refund bounds tests in `tests/test_contract.py`
- replay/idempotency tests in `tests/test_acceptance_matrix.py`
- repeat-alert grouping tests in `tests/test_contract.py`

A related edge case that could still break without careful validation is a malformed refund with a boolean or string value. The current fixes guard against that by rejecting non-integer values before they can affect the balance.

## 6. Unresolved challenge or next step
There is no unresolved failing behavior in the current repository state; the suite is green. The remaining next step would be optional hardening: centralizing validation helpers and expanding edge-case tests around malformed event payloads to make the contract even more explicit.

The main lesson was that the bug was not in one isolated calculation; it was a consistency problem across validation, arithmetic, and state mutation. Fixing those together was necessary to satisfy the rules and keep the ledger behavior trustworthy.