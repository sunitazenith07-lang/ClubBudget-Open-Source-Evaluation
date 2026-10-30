# Reward Rule Notes

## 1. Worked points calculation

Purchase amount: 259,900 paise (₹2,599)

- Points per ₹100: 1
- Bonus percentage: 10%
- Maximum points cap: 100

**Step 1: Base points**

Base points = `(259900 // 10000) * 1`

Base points = `25`

Only complete ₹100 units are counted. Fractional units are discarded using floor division.

**Step 2: Bonus calculation**

Points after bonus = `(25 * (100 + 10)) // 100`

Points after bonus = `27`

The bonus calculation also uses integer floor division.

**Step 3: Apply cap**

Final points = `min(27, 100)`

Final reward = **27 points**

Actual output: `Points example: 27`

## 2. Partial-refund example

Original purchase:
- Amount: 200,000 paise (₹2,000)
- Points per ₹100: 1
- Bonus percentage: 10%
- Initial account balance: 0

**Original points awarded:**

Base points = `(200000 // 10000) * 1 = 20`

Points after bonus = `(20 * 110) // 100 = 22`

Originally awarded points = **22**

**Partial refund:**

Refund amount = 100,000 paise (₹1,000)

Cumulative refunded amount = 100,000 paise

Reversed points = `(22 * 100000) // 200000`

Reversed points = **11**

**Resulting balance:**

Balance after purchase = 22 points

Balance after refund = `22 - 11 = 11 points`

**Relevant ledger entries:**

| Event type | Points delta |
|---|---:|
| purchase_captured | +22 |
| refund_processed | -11 |

Final account balance = **11 points**.

## 3. Three edge cases

**1. Invalid purchase amount**

- Input: `None`, negative amount, string, float, or boolean.
- Expected behaviour: Invalid input should return 0 points.
- Actual observed result: Invalid inputs return 0 points.
- Test: `test_invalid_purchase_amount_returns_zero`

**2. Missing or invalid event identifier**

- Input: Missing, empty, numeric, or boolean event ID.
- Expected behaviour: The event should not award points or create a transaction or ledger entry.
- Actual observed result: The event is rejected without changing the balance or creating a transaction or ledger entry.
- Test: `test_invalid_purchase_event_id_does_not_award`

**3. Refund with insufficient account balance**

- Input: A transaction with one awarded point and an account balance of zero, followed by a full refund.
- Expected behaviour: The account balance must not become negative.
- Actual observed result: The account balance remains zero.
- Test: `test_refund_does_not_make_balance_negative`

## 4. Assumptions and limitations

- **Rounding:** Complete ₹100 units are counted using integer floor division. Bonus points are calculated using integer floor division. The optional cap is applied after the bonus.
- **Missing fields:** Repeat-transaction records with missing or invalid required fields are ignored. Non-dictionary records are also ignored.
- **Repeat-alert threshold:** An alert is generated when the number of matching transactions is greater than the supplied threshold. The default threshold is 2.
- **Refunds:** Refunds are calculated proportionally using integer arithmetic. Cumulative refunds cannot exceed the original transaction amount, and the account balance cannot become negative.
- **Unresolved limitation:** If a customer has already spent some awarded points before receiving a refund, the implementation limits the reversal to the available balance. It does not track the remaining reversal as a pending deduction. This behaviour needs clarification from the project mentor.