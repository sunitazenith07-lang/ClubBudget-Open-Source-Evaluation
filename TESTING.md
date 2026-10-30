# TESTING.md — Required submission

Complete this file with test evidence from your own work. Include at least five edge cases. Do not claim a test passed unless you ran it.

## Test command and environment
- Python version:
    Record the output of python --version
- Command run:
    python -m pytest -q
    python -m main
- Actual test summary:
    214 passed in 0.63 seconds

## Edge-case evidence


## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Same event ID submitted twice | Duplicate event should not be processed again | Duplicate event ignored | Duplicate event test |
| 2 | Purchase amount is negative | Invalid purchase should be rejected | No points added | Invalid purchase amount test |
| 3 | Refund exceeds original purchase amount | Refund should be rejected | Balance remains unchanged | Refund limit test |
| 4 | Refund amount is zero or negative | Invalid refund should be rejected | No points reversed | Invalid refund test |
| 5 | Refund for a non-existing transaction | Refund should be rejected | Account remains unchanged | Unknown transaction refund test |


## Regression tests added
List the defects fixed and the tests added to prevent them from returning.
    No new test files or test cases were added during this work.
    Existing automated tests were used to verify the fixes.
    The existing tests cover reward calculation, duplicate event handling, refund validation, and transaction behaviour.
    The final test run completed with 214 passing tests.

## Remaining failures or limitations
List any known failing tests or unresolved behaviours honestly.
    The final automated test run reported zero failures.
    No separate performance benchmark was conducted.
    Further testing of unusual transaction sequences and multiple partial refunds would be useful.
    Additional independent tests could provide further confidence in ledger consistency and refund calculations.
