# approach.md - Required submission

Complete this file in your own words. Be concise and specific to the work you actually performed.

## 1. Baseline
- Commands run before editing:
    python -m pip install -r requirements-dev.txt
    python -m pytest -q
    python -m main

- Initial test result (include the actual summary):
    After the first reward calculation changes, 169 tests passed and 45 tests failed.
    After investigating and making further changes, all 223 tests passed.

- Demo/output observed:
    Points example: 27
    Repeat warnings: []
    The main application executed successfully.

## 2. Codebase understanding
- Important files/functions inspected:
    models.py
    service.py
    main.py

- Rewards calculation, refund, ledger or alert flow traced:
    The models.py file initializes customer accounts with a points balance, processed event IDs, transactions, and a ledger.
    The service.py file contains the main reward-processing functions, including reward calculation, purchase processing, refund handling, and repeat transaction detection.

- How you confirmed your understanding:
    I understood the transaction flow by examining the existing functions and comparing their behavior with the automated test result.

## 3. Investigation and implementation strategy
For each major defect, describe the symptom, hypothesis, evidence from a test/log/example, and the fix chosen.
- Issue 1:
    Symptom: The starter calculation used floating-point division and rounding.
    Evidence: The original implementation used Python's round() function.
    Change: Updated the calculation to use integer floor division, input validation, promotional bonuses, and optional points caps.

- Issue 2:
    Symptom: Repeated event IDs were being recorded more than once.
    Evidence: Tests reported duplicate event IDs in the processed events list.
    Change: Added duplicate event ID checking before processing events.

- Issue 3 (if applicable):
    Symptom: Invalid and excessive refunds were not handled safely.
    Evidence: Tests identified problems with negative values, Boolean values, invalid types, and refunds exceeding the original purchase amount.
    Change: Added refund input validation, refund boundary checks, and cumulative refund calculations.

## 4. Implementation decisions
- Main changes and why:
    Used integer arithmetic to avoid floating-point rounding problems.
    Added input validation to reject invalid values.
    Added duplicate event protection to prevent repeated processing.
    Used cumulative refund amounts to calculate proportional point reversals.
    Maintained transaction and ledger records for accepted events.

- Alternatives considered and why rejected:
    Floating-point rounding was avoided because the reward calculation requires integer arithmetic.
    Unrestricted refund processing was avoided because refunds must not exceed the original purchase amount.

- Assumptions:
    Only valid captured purchases are eligible for reward points.
    Each event ID should be processed only once.
    Refunds must be valid and within the remaining refundable amount.

## 5. Verification
- Tests added or changed:
    Existing automated tests were used to verify the changes. No new test additions are claimed here.

- Commands run and actual results:
    Existing automated tests were used to verify the changes. No new test additions are claimed here.

- Edge cases verified:
    Negative reward amounts.
    Zero points cap.
    Duplicate purchase events.
    Negative refund amounts.
    Invalid refund data types.
    Refunds exceeding the original purchase amount.
    Partial refunds.

- Remaining failures or known limitations:
    No failures were reported by the final 214-test run.
    Additional behavior should still be checked against the complete evaluation requirements.

Record actual engineering decisions and evidence. Do not claim tests or experiments you did not run.

