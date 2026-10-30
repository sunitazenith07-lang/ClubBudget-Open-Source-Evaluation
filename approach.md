# My Approach — RewardBook

## 1. What I understood from the task

The task was to work on the reward points system. It should give points for captured purchases, handle refunds, and identify transactions that look repeated.

The main things I focused on were:

- Calculating points correctly using integer arithmetic.
- Giving points only for captured purchases.
- Making sure the same event is not processed again.
- Reversing points when a refund happens.
- Keeping the points balance correct.
- Keeping a ledger entry for accepted purchase and refund events.
- Finding similar transactions so they can be checked manually.

## 2. First, I checked the existing files

I went through the project files to understand how the code was arranged.

- `models.py` creates the account structure. It has the balance, processed event IDs, transactions and ledger.
- `fixtures.py` contains sample accounts, transactions and reward rules.
- `service.py` has the main reward calculation, event processing and repeat-transaction logic.
- `main.py` runs a small example.
- `tests/` contains the contract tests and acceptance tests.

Most of my implementation work was in `service.py`.

## 3. I ran the tests before making changes

Before changing the code, I ran the test suite to see what was already failing.

The result was:

```text
147 passed, 67 failed
```

The failures were mainly related to:

- Reward points calculation.
- Bonus and cap handling.
- Processing the same event more than once.
- Purchase transaction details.
- Refund amount validation.

I saved this output in `baseline-test-results.txt`.

## 4. Changes I made

### A. Reward points calculation

I changed the calculation to use integer floor division instead of floating-point rounding.

```python
base = (amount_paise // 10000) * points_per_100_rupees
```

The bonus is calculated after the base points, and the cap is applied at the end. I also made sure that a cap of zero is accepted.

### B. Duplicate event check

I added a check for event IDs that have already been processed.

If the same event comes again, the function returns without applying it again.

### C. Refund validation

I added checks for refund values. The code rejects values that are not integers, values that are zero or negative, and refunds that go beyond the remaining purchase amount.

### D. Partial refund calculation

For a partial refund, I used the total refunded amount to calculate how many points should be reversed.

The code then subtracts only the difference between the new reversal amount and the points already reversed. This helps avoid reversing the same points again.

### E. Repeat transaction check

I grouped transactions using account ID, date and amount.

If the number of matching transactions is greater than the given threshold, the group is returned as a possible repeat. These results are only for review.

## 5. How I checked the changes

After making the changes, I ran:

```bash
python -m pytest -q
```

The final result was:

```text
214 passed
```

I also ran:

```bash
python -m main
```

The output was:

```text
Points example: 27
Repeat warnings: []
```

## 6. What can be improved next

The current implementation uses the in-memory account and transaction structures provided in the project.

Some things that still need more work are:

- Checking missing event IDs and transaction IDs.
- Checking invalid purchase amounts and reward-rule values.
- Adding more tests for these invalid inputs.
- Using a database to store account and transaction data.
- Handling multiple events safely when they are processed at the same time.