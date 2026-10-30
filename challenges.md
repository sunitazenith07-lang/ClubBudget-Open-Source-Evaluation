# challenges.md - COMPULSORY submission

This file is mandatory and worth 5 marks. Describe your actual experience honestly. Do not invent difficulties to fill the page.

## 1. Challenge or confusing behaviour
What specific calculation, event, test failure, refund rule, ledger entry, or repeat-alert case was difficult to understand?

Understanding why reward calculations were using incorrect rounding.
Preventing duplicate purchase events from being processed more than once.
Understanding how partial refunds should proportionally reverse reward points.
Handling invalid refund inputs such as negative values, strings, Boolean values, and excessive refund amounts.

## 2. Evidence
Summarize the relevant assertion, output, error, or minimal example. Do not include secrets or real customer data.

After my initial reward calculation changes, 169 tests passed and 45 tests failed.
Duplicate purchase event tests showed that the same event ID could appear more than once in the processed event list.
Refund tests identified problems with negative refund amounts, invalid data types, and refunds exceeding the original purchase amount.

## 3. What I tried
List the debugging steps or experiments you actually performed and what each one showed.

Inspected the reward calculation and transaction-processing functions in service.py.
Reviewed account initialization in models.py.
Updated transaction processing to handle duplicate events and invalid refunds.
## 4. Resolution
What was the root cause? What did you change, and why did it fix the cause rather than hide the symptom?

Used integer floor division for reward calculations.
Added validation for negative and invalid reward inputs.
Added duplicate event ID checking.
Added refund amount validation.
## 5. Proof and regression prevention
Which test(s) demonstrate the fix? What related case could still break?

Final test result:
214 passed in 0.70s

I also ran the main application successfully.
Observed output:
Points example: 27
Repeat warnings: []

## 6. Unresolved challenge or next step
State remaining limitations and how you would investigate them next.

The final automated test run reported no failures.
Further investigation could focus on additional boundary cases, multiple partial refunds, unusual event sequences, and maintaining ledger consistency.

If you did not encounter a major blocker, say so honestly and document the hardest edge case you deliberately tested and what it taught you. Do not manufacture a story.