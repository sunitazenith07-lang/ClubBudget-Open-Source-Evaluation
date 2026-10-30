# approach.md - Required submission

Complete this file in your own words. Be concise and specific to the work you actually performed.

## 1. Baseline
- Commands run before editing: python -m pytest -q and python -m main.
- Initial test result (include the actual summary): 67 failed and 147 passed.
- Demo/output observed:The starter implementation's initial demo was run. The final demo output after implementation was:

Points example: 27

Repeat warnings: []

## 2. Codebase understanding
- Important files/functions inspected: service.py, models.py, fixtures.py, main.py, tests/test_acceptance_matrix.py, and tests/test_contract.py. I also reviewed the problem statement and repository instructions.

- Rewards calculation, refund, ledger or alert flow traced:
⚪ calculate_points() calculates purchase rewards from the amount and reward rules.
⚪ apply_reward_event() processes captured purchases and refunds, updates the account balance, tracks processed event IDs, and writes ledger entries.
⚪ flag_repeat_transactions() groups transactions by account, date, and amount, then compares each group against the supplied threshold.

- How you confirmed your understanding: I compared the implementation with the acceptance tests, ran the starter tests, and added focused regression tests for behaviours that were not adequately covered.

## 3. Investigation and implementation strategy
For each major defect, describe the symptom, hypothesis, evidence from a test/log/example, and the fix chosen.
- Issue 1: Incorrect points calculation

Symptom: The starter implementation used rounding when calculating complete ₹100 units.

Evidence: The acceptance tests included boundary amounts such as 9,999, 10,000, and 19,999 paise.

Fix: Replaced floating-point rounding with integer floor division. Applied the bonus using integer arithmetic and applied the optional cap after the bonus.

- Issue 2: Event validation and refund handling

Symptom: The starter implementation did not adequately protect against duplicate events and invalid or excessive refunds.

Evidence: The refund and event tests covered replayed events, invalid refund amounts, excessive refunds, and unknown transactions.

Fix: Added event ID and transaction ID validation, duplicate-event protection, refund amount validation, refund bounds checking, proportional integer reversal, and a balance safeguard.

- Issue 3 (if applicable): Repeat-alert handling of malformed records

Symptom: Records with missing fields could be grouped together, and non-dictionary records could raise an exception.

Evidence: Two regression tests initially failed:

Missing fields produced a false repeat alert.

A None record raised an AttributeError.

Fix: Added validation for the input list, threshold, record type, account ID, date, amount, and transaction ID before grouping records.

## 4. Implementation decisions
- Main changes and why:
- Alternatives considered and why rejected:
- Assumptions:
⚪ A repeat alert is generated when the number of matching records is greater than the supplied threshold.

⚪ Invalid identifiers and malformed repeat records should be ignored safely.

⚪ Refunds must not exceed the remaining refundable purchase amount or reduce the account balance below zero.

## 5. Verification
- Tests added or changed: Added regression tests in tests/test_contract.py for invalid calculation inputs, missing event and transaction identifiers, negative-balance protection, empty repeat-alert input, single transactions, missing transaction fields, and non-dictionary records.

- Commands run and actual results:
⚪ Initial baseline: python -m pytest -q — 67 failed, 147 passed.

⚪ Contract tests after the final additions: python -m pytest tests/test_contract.py -q — 45 passed.

⚪ Final full suite: python -m pytest -q — 247 passed.

⚪ Demo: python -m main — Points example: 27, Repeat warnings: [].

⚪ Diff validation: git diff --check — no errors reported.

- Edge cases verified:
⚪ Amounts below and exactly at a ₹100 boundary.

⚪ Invalid and negative reward calculation inputs.

⚪ Zero reward cap.

⚪ Replayed purchase events.

⚪ Invalid and excessive refunds.

⚪ Missing event and transaction identifiers.

⚪ Refunds that must not make the balance negative.

⚪ Empty repeat-alert input and a single transaction.

⚪ Missing fields and non-dictionary repeat records.

- Remaining failures or known limitations: The specification does not define how to recover a proportional refund reversal when the account has already spent some of its awarded points. The current implementation limits deductions to the available balance to prevent a negative balance. A deferred-reversal mechanism has not been implemented.

Record actual engineering decisions and evidence. Do not claim tests or experiments you did not run.
