# TESTING.md — Required submission

## Test command and environment
- Python version:
Python version used in the project environment (confirm using python --version).
- Command run:
python -m pytest -q
- Actual test summary:
Initial run: 67 failed, 147 passed (214 tests).

Final run: 214 passed in 0.15s.

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |
#

Case / input

Expected behaviour

Actual result

Test name or evidence

1

Purchase of ₹99.99

Should earn 0 points at 1 point per ₹100.

Correctly returns 0 points.

Purchase boundary test

2

Purchase of ₹100.00

Should earn 1 base point at 1 point per ₹100.

Correctly returns 1 point.

Purchase boundary test

3

cap_points = 0

Reward points should be limited to 0.

Correctly returns 0 points.

Zero-cap test

4

Processing the same event ID twice

Points should not be awarded twice.

Duplicate event is ignored.

Duplicate event test

5

Full and partial refunds

Points should be reversed proportionally without making the balance negative.

Refund calculations are handled correctly.

Refund tests

6

Refund greater than the remaining refundable amount

Invalid excessive refund should be rejected.

Account remains unchanged.

Refund validation test

7

Refund for a non-existent transaction

No points should be reversed.

Account remains unchanged.

Invalid transaction test


## Regression tests added
List the defects fixed and the tests added to prevent them from returning.
The following defects were fixed and checked using the existing test suites:

Rounding errors: Checked purchase amounts around ₹100 boundaries.

Zero-cap handling: Checked that cap_points = 0 is accepted.

Duplicate events: Checked that the same event cannot be processed twice.

Refund calculation: Checked full and partial refunds.

Excessive refunds: Checked that refunds beyond the remaining amount are rejected.

## Remaining failures or limitations
List any known failing tests or unresolved behaviours honestly.
No known failing tests remain in the final test run.

Final test result: 214 passed in 0.15s.

Performance and memory usage were not separately benchmarked.

Further testing with larger transaction histories and additional refund combinations could improve confidence.