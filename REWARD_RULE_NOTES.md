# REWARD_RULE_NOTES.md — Required submission

Complete this file with your own actual examples and results. Do not leave prompts unanswered.

## 1. Worked points calculation
Show one purchase calculation from amount in paise through base points, bonus and cap. State the rounding rule at each step and include the actual output.
Example purchase:

- Purchase amount: 25,000 paise (₹250)
- Points per 100 rupees: 10
- Bonus percentage: 25%
- Maximum points cap: 22

Step 1: Calculate base points.

The system awards points only for complete ₹100 units.

25,000 // 10,000 = 2

Base points = 2 × 10 = 20

Step 2: Apply bonus.

Bonus points = (20 × 25) // 100 = 5

Points after bonus = 20 + 5 = 25

Step 3: Apply points cap.

Final points = min(25, 22) = 22

Actual output: 22 points.

Rounding rule:
Integer floor division (//) is used. Partial ₹100 amounts do not earn additional base points. Bonus calculations also use floor division. The points cap is applied after the bonus.


## 2. Partial-refund example
Show the points originally awarded, the refund amount, how the reversal is calculated, the resulting balance, and the relevant ledger entry.
Example purchase:

- Original purchase amount: 50,000 paise (₹500)
- Points per 100 rupees: 10
- Bonus percentage: 20%
- Points originally awarded: 60
- Refund amount: 25,000 paise (₹250)

Step 1: Calculate original points.

Base points = (50,000 // 10,000) × 10
Base points = 5 × 10 = 50

Bonus points = (50 × 20) // 100 = 10

Total points awarded = 50 + 10 = 60

Step 2: Calculate the partial refund reversal.

Reversal = (60 × 25,000) // 50,000

Reversal = 30 points

Step 3: Calculate remaining points.

Remaining points = 60 - 30 = 30

Result:
- Original points awarded: 60
- Refund amount: 25,000 paise
- Points reversed: 30
- Remaining points balance: 30

Relevant ledger entry:

{
  "type": "refund_processed",
  "points_delta": -30
}


## 3. Three edge cases
For each, provide input, expected behaviour, actual observed result, and the test that verifies it.
1.Case 1: Duplicate event ID

Input:
Submit the same event ID more than once.

Expected behaviour:
The same event should not be processed twice.

Actual observed result:
The duplicate event is ignored and no additional points are awarded.

Test evidence:
Duplicate event handling test.

2.Case 2: Invalid purchase amount

Input:
A purchase event with a negative amount.

Expected behaviour:
The invalid purchase should be rejected.

Actual observed result:
The account balance remains unchanged.

Test evidence:
Invalid purchase amount test.

3.Case 3: Refund exceeds purchase amount

Input:
A refund amount greater than the remaining refundable purchase amount.

Expected behaviour:
The refund should be rejected.

Actual observed result:
The account balance and transaction refund amount remain unchanged.

Test evidence:
Refund limit validation test.



## 4. Assumptions and limitations
Document rounding assumptions, missing-field handling, repeat-alert threshold assumptions, and any unresolved issue.
Rounding assumptions
- Points are calculated using complete ₹100 units.
- Integer floor division is used for base points.
- Bonus points are rounded down using integer division.
- The maximum points cap is applied after the bonus calculation.
- Partial refunds reverse points proportionally using integer floor division.

### Missing-field handling
- Missing or invalid event IDs are rejected.
- Missing or invalid transaction IDs are rejected.
- Missing or invalid purchase/refund amounts are rejected.
- Missing reward rule values use the defaults defined in the code.

### Repeat-alert threshold
The repeat transaction detection function uses a default threshold of 2.
A group is reported only when its transaction count is greater than the threshold.

### Limitations
- The repeat transaction detection uses account ID, date, and amount to identify repeated transactions.
- Transactions with different dates or amounts may not be grouped together.
- No performance benchmark was conducted.
- Any unresolved issues should be documented after reviewing the final test results.


