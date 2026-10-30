# Optimizations — RewardBook

## 1. What I found in the first test run

When I ran the tests before changing the code, I got:

```text
147 passed, 67 failed
```

The main issues were:

- Reward points were not always calculated correctly.
- A zero points cap was not being applied.
- Duplicate events were not handled properly.
- Refund values were not validated properly.
- Some transaction and reward records were not matching the expected behaviour.

## 2. Improvements I made

### A. Changed reward calculation to integer arithmetic

Earlier, the calculation used floating-point division and rounding. I changed it to integer floor division:

```python
base = (amount_paise // 10000) * points_per_100_rupees
```

This gives the expected result at the ₹100 boundaries and avoids floating-point rounding issues.

### B. Fixed the points cap

I used a `None` check for the cap instead of checking whether the value is true or false.

This means a cap of zero is also applied correctly.

### C. Added duplicate event protection

I added an early check for event IDs that have already been processed.

This stops the same event from being applied again and keeps the processed-event list consistent.

### D. Added refund checks

Before changing the transaction, the code checks the refund value.

It rejects non-integer values, zero or negative values, and refunds that exceed the remaining refundable amount.

### E. Improved partial refund calculation

The code calculates the total points that should be reversed based on the cumulative refunded amount.

Only the difference from the previous reversal is deducted. This supports multiple partial refunds without reversing the same points twice.

### F. Grouped repeat transactions

I grouped transactions using account ID, date and amount.

This helps find similar transactions while keeping different accounts and dates separate. The results are only alerts for manual review.

## 3. Some trade-offs in the current code

| What I used | Why I used it | Limitation |
|---|---|---|
| Integer arithmetic | Keeps reward calculations predictable | I need to be careful about using paise and rupees correctly |
| Deep copy of account | Keeps the original account unchanged | It uses extra memory |
| List of processed event IDs | Simple way to check duplicate events | Searching the list can become slower when it grows |
| In-memory transaction data | Easy to work with in this project | Data is not permanently stored |
| Dictionary grouping | Makes it easy to group similar transactions | Transaction fields should be present and consistent |

## 4. Improvements I would work on next

These are ideas for future work. They are not implemented as part of the current changes.

1. **Database storage:** Store account balances, transactions and ledger entries in a database.
2. **Unique event IDs:** Use a database-level unique constraint so duplicate events are also handled safely when multiple requests come together.
3. **Identifier checks:** Reject events with missing or empty event IDs and transaction IDs.
4. **Input validation:** Check purchase amounts and reward-rule values before processing.
5. **Ledger checks:** Verify that the account balance matches the accepted ledger entries.
6. **Faster repeat detection:** Use database indexes or grouped queries when there are many transactions.
7. **Monitoring:** Keep track of rejected events, refund failures and repeat alerts.

## 5. Final test result

After making the changes, I ran the full test suite again:

```bash
python -m pytest -q
```

The result was:

```text
214 passed
```

The main focus of my changes was fixing the correctness issues found in the first test run, rather than trying to optimize performance before it was needed.