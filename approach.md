# Approach

## 1. Baseline

Before making any changes, I ran the following commands to understand the existing project and check how it was working:

- `python -m pytest -q`
- `python -m main`
- `python --version`

**Environment:** Python 3.14.4 on Windows.

**Initial test result:**
- 67 tests failed.
- 147 tests passed.
- Total: 214 tests.

I also noticed that the demo showed:

```text
Points example: 28
Repeat warnings: []
```

After checking the calculation, I found that the points example was incorrect. For a purchase of ₹2,599, the correct calculation should give 27 points, not 28.

The main problems I found were:

1. The points calculation used `round()`, which sometimes gave extra points for amounts just below a ₹100 boundary.
2. A reward cap of zero was ignored because the code used `if cap_points:`.
3. Duplicate purchase events could be processed more than once.
4. Refunds could exceed the original purchase amount.
5. Invalid refund values, such as negative numbers and booleans, were not handled properly.

These problems were the main things I focused on fixing.

## 2. Understanding the Codebase

Before changing the code, I went through the important files to understand how the project worked.

The main files I checked were:

- `service.py` – Contains the points calculation, reward event processing and repeat transaction checking.
- `models.py` – Contains the function that creates a new account and its default structure.
- `fixtures.py` – Provides sample data for the project.
- `data/records.json` – Contains the larger sample dataset.
- `tests/test_contract.py` – Contains tests for the expected behaviour.
- `tests/test_acceptance_matrix.py` – Contains different input cases to check the reward rules.

I mainly focused on understanding three flows.

### Purchase flow

When a purchase event is received, the program first checks whether its event ID has already been processed.

If it is a new event, the program checks the transaction details and reward rules. Only a valid captured purchase can earn points.

The points are calculated using integer division. After calculating the base points and bonus, the program applies the cap if one is provided.

The transaction is then saved, the points balance is updated, and an entry is added to the ledger.

### Refund flow

For a refund, the program first checks whether the original transaction exists and whether the refund amount is valid.

It also checks that the total refunded amount does not exceed the original purchase amount.

Points are reversed based on the total refunded amount so that multiple partial refunds do not create rounding differences.

The actual deduction is limited to the points currently available in the account, so the balance does not become negative.

### Repeat transaction alerts

The program groups transactions using the account ID, date and amount.

If the number of matching transactions is greater than the given threshold, it creates an alert for review.

These alerts are only warnings. They do not block transactions or automatically mark anyone as doing something wrong.

## 3. Problems I Found and How I Fixed Them

### Problem 1: Incorrect points calculation

**What was happening?**

The old calculation used `round()`. Because of this, an amount just below ₹100 could sometimes earn points for the next ₹100 bracket.

For example, ₹199.99 should earn points for ₹100, not ₹200.

**What I changed:**

I replaced `round()` with integer division (`//`).

```python
base_points = (amount_paise // 10000) * points_per_100_rupees
```

I also used integer arithmetic for the bonus calculation:

```python
points = (base_points * (100 + bonus_percent)) // 100
```

This follows the reward calculation rules without relying on floating-point rounding.

### Problem 2: Cap of zero was not working

**What was happening?**

The old code used:

```python
if cap_points:
```

In Python, zero is treated as `False`. Because of this, a cap of zero was ignored.

**What I changed:**

I changed the condition to:

```python
if cap_points is not None:
```

Now a cap of zero is also applied correctly. I also added checks for invalid and negative cap values.

### Problem 3: Duplicate events were processed again

**What was happening?**

When the same event was received again, the program could process it again and update the account balance more than once.

**What I changed:**

I added a check at the beginning of `apply_reward_event()` to see whether the event ID was already present in `processed_event_ids`.

If it was already processed, the function returns without making another change.

This helps prevent duplicate purchases and refunds from changing the account more than once.

### Problem 4: Invalid refunds were accepted

**What was happening?**

The old code did not properly check refund amounts. Negative values, invalid types and refunds greater than the original purchase amount could cause incorrect account updates.

**What I changed:**

I added validation for refund amounts. The refund must be a positive integer, and boolean values are rejected separately because Python treats booleans as integers.

I also added a check to make sure that the total refunded amount never exceeds the original purchase amount.

## 4. Implementation Decisions

While making the changes, I tried to keep the existing project structure intact.

Some important decisions I made were:

- I kept the existing account and transaction dictionary structure so that other parts of the project would continue working.
- I used integer division instead of floating-point calculations for reward points.
- I checked boolean values separately from integers to avoid accepting `True` or `False` as valid amounts.
- I used cumulative refund calculations instead of calculating every partial refund separately. This helps avoid losing points because of repeated rounding.
- I added a CSV statement export function as an extra feature for viewing account transaction details.

### Why I used cumulative refund calculation

Suppose an account receives 10 points for a purchase and the customer makes multiple partial refunds.

Instead of calculating the points to reverse independently for every refund, I calculate the total points that should have been reversed based on the total refunded amount.

This helps keep the final reversal accurate when several partial refunds are made.

### Assumptions

I followed these assumptions while working on the project:

- All transaction amounts are stored as integer paise.
- ₹1 = 100 paise.
- Only captured purchases earn reward points.
- Repeat transaction alerts are only for human review.
- A refund cannot exceed the original purchase amount.

## 5. Testing and Verification

I kept the existing tests and added a new test file:

`tests/test_fintech_edge_cases.py`

The new tests cover different situations, including:

- Normal and invalid purchases.
- Negative amounts and invalid reward rules.
- Zero reward caps.
- Duplicate purchase and refund events.
- Full and partial refunds.
- Refunds made in multiple steps.
- Missing transaction and event IDs.
- Cases where the available points balance is lower than the required refund reversal.
- CSV statement generation.

I also checked that the transaction and ledger structures remained compatible with the existing project.

### Final test results

After making the changes, I ran the tests and demo again.

**Command:**

```powershell
python -m pytest -q
```

**Output:**

```text
248 passed in 0.27s
```

I also ran:

```powershell
python -m main
```

**Output:**

```text
Points example: 27
Repeat warnings: []
```

### Some important edge cases checked

1. An amount of 9999 paise should earn zero base points at a rate of 1 point per ₹100.
2. A reward cap of zero should return zero points.
3. Negative reward rules and invalid amounts should not generate points.
4. Multiple partial refunds should calculate the total reversal correctly.
5. The account balance should never become negative because of a refund.

### Known limitation

If a customer has already spent some of their awarded points outside this service, a refund cannot deduct more points than the balance currently available.

For example, if 10 points need to be reversed but only 2 points remain, the service deducts 2 points. The transaction records the full calculated reversal, but the remaining 8 points are not recovered by the current implementation.

This behaviour prevents a negative balance, but it does not handle outstanding reward liabilities. A separate business rule would be needed for that.

### Final result

The final test run completed with 248 passing tests. The demo also produced the expected points example of 27. The changes were tested against the existing test suite as well as the additional edge cases.