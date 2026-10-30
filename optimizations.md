# Optimizations

## 1. What Needed Improvement

While working on the project, I found a few areas that needed improvement.

- **Points calculation:** The old code used `round()` for calculating points. This could give incorrect results for purchases just below a ₹100 boundary.
- **Duplicate events:** The same event could be processed more than once, which could increase the points balance incorrectly.
- **Input validation:** Some invalid values, such as negative numbers, booleans and incorrect data types, were not handled properly.
- **Refund handling:** Multiple partial refunds could cause rounding differences, and refunds greater than the original purchase amount were not rejected.
- **Repeat transaction checking:** The alert function needed to group transactions properly and produce consistent results.

My main goal was to make the reward calculation more accurate and make the event processing safer.

## 2. Options I Considered

### Option 1: Using the Decimal library

One option was to use Python's `Decimal` library for calculations.

It provides better control over decimal calculations and rounding. However, the project already stores transaction amounts in paise as integers.

I decided to use integer arithmetic instead because it was simpler and directly followed the reward calculation rules.

### Option 2: Using a set for duplicate event checking

A Python set can check whether an event ID already exists faster than a list in most cases.

However, the existing account structure uses a list for `processed_event_ids`. I kept that structure unchanged to avoid affecting the existing project and its tests.

For the current project size, list-based checking was sufficient.

### Option 3: Grouping repeat transactions in one pass

Another improvement was to group transactions using their account ID, date and amount.

I used a dictionary to group matching transactions in one pass. After grouping, the program checks which groups have crossed the given threshold.

This also helps keep the alert results consistent.

## 3. Changes I Made

### Change 1: Improved points calculation

I replaced `round()` with integer floor division.

```python
base_points = (amount_paise // 10000) * points_per_100_rupees
points = (base_points * (100 + bonus_percent)) // 100
```

This makes sure that customers only receive points for complete ₹100 amounts.

I also fixed the zero-cap issue and added validation for invalid reward rules.

**Testing:** I checked the points calculation and bonus/cap cases using the existing test suite.

### Change 2: Added duplicate event checking

I added a check at the beginning of event processing.

If an event ID has already been processed, the program returns without applying the same event again.

This prevents duplicate point awards and repeated ledger entries when the same event is received again.

**Testing:** I checked duplicate purchase and refund events to make sure they do not change the account a second time.

### Change 3: Improved partial refund calculation

I changed the refund calculation to use the total refunded amount instead of calculating every refund separately.

This helps avoid losing points due to rounding when a transaction has multiple partial refunds.

I also added checks for invalid refund amounts and refunds greater than the original purchase amount.

**Testing:** I checked multiple partial refunds, full refunds and rounding cases.

### Change 4: Added CSV statement export

As an extra feature, I added `generate_account_statement_csv()`.

It uses Python's built-in `csv` module and `StringIO` to generate an account statement in CSV format.

This can be useful for viewing and reviewing transaction records.

**Testing:** I added a test to check whether the CSV statement is generated correctly.

## 4. Testing Results

I ran the test suite before and after making the changes.

**Initial result:**

```text
214 tests
67 failed
147 passed
```

**Latest result:**

```text
248 passed in 0.27s
```

The latest test run passed all 248 tests.

The demo also produced:

```text
Points example: 27
Repeat warnings: []
```

The baseline and final test runs had different numbers of tests, so I am not treating their execution times as a direct performance comparison. The main improvement I verified was in correctness and test coverage.

## 5. Trade-offs

### Using deepcopy

The `apply_reward_event()` function uses `deepcopy(account)` to work on a separate copy of the account.

This helps prevent changes made during processing from directly affecting the original account object.

The downside is that copying data takes extra memory and processing time. For this evaluation, keeping the original account unchanged was more important than optimizing this small operation.

### Strict input validation

I added checks to reject invalid types, including boolean values.

This makes the code slightly longer, but it prevents incorrect values from being accepted as valid transaction amounts.

For a reward system, avoiding incorrect balance updates is more important than accepting every possible input.

## 6. Further Improvements

There are a few things that could be improved if the project were developed further.

1. **Better data validation:** Pydantic or dataclasses could be used to make account, transaction and reward rule validation more structured.

2. **Database-based ledger:** The current project stores data using Python dictionaries. A database with an append-only ledger would be more suitable for a real financial application.

3. **Better repeat transaction detection:** The current system groups transactions by account, date and amount. It could be extended to check transactions within smaller time periods, such as 15 minutes.

4. **Handling points already spent:** A separate rule could be added for cases where a customer has already spent the points that need to be reversed after a refund.