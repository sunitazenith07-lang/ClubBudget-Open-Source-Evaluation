# challenges.md - COMPULSORY submission

This file is mandatory and worth 5 marks. Describe your actual experience honestly. Do not invent difficulties to fill the page.

## 1. Challenge or confusing behaviour
What specific calculation, event, test failure, refund rule, ledger entry, or repeat-alert case was difficult to understand?
While working on RewardBook, I faced four main challenges:

Rounding errors: Reward points were calculated incorrectly near ₹100 boundaries.

Zero-cap problem: The program ignored cap_points = 0.

Duplicate events: The same event could be processed multiple times, adding points repeatedly.

Refund calculations: Partial refunds caused rounding differences, and excessive refunds were not properly handled.

I also investigated how ledger entries and repeat transaction alerts worked.

## 2. Evidence
Summarize the relevant assertion, output, error, or minimal example. Do not include secrets or real customer data.
Initially, I ran:

python -m pytest -q

Initial result: 67 failed, 147 passed (214 tests total) in 0.18s.

The failures were mainly related to rounding, zero caps, duplicate events, and refund validation.

For example, ₹199.90 could incorrectly count as 2 complete ₹100 units instead of 1.

## 3. What I tried
List the debugging steps or experiments you actually performed and what each one showed.
Inspected service.py and its main functions.

Reviewed failing assertions in tests/test_acceptance_matrix.py.

Compared the implementation with STUDENT_PROBLEM_STATEMENT.md.

Tested purchase amount boundaries and zero caps.

Investigated duplicate event processing.

Checked full, partial, and excessive refund scenarios.

Ran pytest after individual fixes to verify progress.

## 4. Resolution
What was the root cause? What did you change, and why did it fix the cause rather than hide the symptom?
I fixed the identified problems:

Rounding: Replaced round() with integer floor division (//).

Zero cap: Used cap_points is not None to accept zero as a valid cap.

Duplicate events: Added event ID checking using processed_event_ids.

Refunds: Added refund validation and cumulative point reversal to prevent excessive refunds and rounding drift.

## 5. Proof and regression prevention
Which test(s) demonstrate the fix? What related case could still break?
I verified the fixes using the existing test suites.

Important cases checked:

₹99.99 and ₹100.00 purchase boundaries.

Zero reward points cap.

Duplicate event prevention.

Full and partial refunds.

Excessive and invalid refunds.

Refunds for non-existent transactions.

Final test result:

python -m pytest -q

214 passed in 0.15s.

I kept the existing test suites intact and used them to check that the fixes did not break other functionality.

A further case worth testing is a large number of partial refunds in different sequences.

## 6. Unresolved challenge or next step
State remaining limitations and how you would investigate them next.

If you did not encounter a major blocker, say so honestly and document the hardest edge case you deliberately tested and what it taught you. Do not manufacture a story.
There are no known failing tests in the final implementation.

The most challenging case was handling multiple partial refunds without rounding differences.

As a future improvement, I would test larger transaction histories, more unexpected event inputs, and additional refund combinations to improve reliability.