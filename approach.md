# approach.md

## 1. Baseline

- **Commands run before editing:**
  - `python -m pip install -r requirements-dev.txt`
  - `python -m pytest -q`
  - `python -m main`
- **Initial test result:** `67 failed, 147 passed in 1.30s`.
- **Demo/output observed:** Ran the main module using `python -m main`. The exact demo output was not recorded in my notes.

## 2. Codebase understanding

- **Important files/functions inspected:** Inspected the reward calculation, event processing, and repeat transaction alert logic, mainly `calculate_points()`, `apply_reward_event()`, and `flag_repeat_transactions()`.
- **Flow traced:**
  - Reward points are calculated from the purchase amount, points rate, bonus percentage, and optional cap.
  - Captured purchases create transaction records and add points to the account balance.
  - Refunds calculate the points that need to be reversed and update the balance and ledger.
  - Repeat transaction alerts group transactions using account ID, date, and amount.
- **How I confirmed my understanding:** Compared the existing implementation with the expected behaviour and used the test failures and examples to identify incorrect calculations and missing validations.

## 3. Investigation and implementation strategy

- **Issue 1: Incorrect reward calculation**
  - **Symptom:** The original calculation used `round()` on the purchase amount, which could give incorrect points around amount boundaries.
  - **Hypothesis:** Reward points should be based on complete ₹100 units, not rounded amounts.
  - **Evidence:** The initial test run reported 67 failures.
  - **Fix:** Replaced floating-point rounding with integer floor division (`amount_paise // 10000`). Calculated the bonus using integer arithmetic and applied the cap after the bonus.

- **Issue 2: Incorrect cap handling and input validation**
  - **Symptom:** A cap of zero was not applied because the original code checked the cap using `if cap_points`.
  - **Hypothesis:** The code should distinguish between a missing cap and a valid zero cap.
  - **Evidence:** The zero-cap and invalid-input cases were included in the regression checks.
  - **Fix:** Used `cap_points is not None` and added `valid_int()` to validate non-negative integer values while excluding booleans.

- **Issue 3: Duplicate events and refund handling**
  - **Symptom:** Repeated event IDs could be processed again, and refund amounts were not properly restricted by the original purchase amount.
  - **Hypothesis:** Each event should be processed only once, and cumulative refunds should never exceed the original purchase.
  - **Evidence:** Added regression tests for duplicate events, refunds greater than the purchase, unknown transactions, and partial refunds.
  - **Fix:** Added duplicate event checks, validated transaction and refund details, calculated proportional reversals using integer arithmetic, and updated the transaction record, balance, and ledger.

## 4. Implementation decisions

- **Main changes and why:**
  - Added `valid_int()` for consistent non-negative integer validation.
  - Used integer arithmetic to avoid floating-point rounding issues.
  - Added duplicate event protection using `processed_event_ids`.
  - Stored purchase amount, awarded points, reversed points, and refunded amount in transaction records.
  - Added refund validation and proportional point reversal.
  - Preserved the existing repeat transaction grouping logic.

- **Alternatives considered and why rejected:**
  - Kept integer arithmetic instead of floating-point calculations because reward amounts and point reversals need predictable results.
  - Kept the existing repeat transaction grouping approach because it already groups transactions by account, date, and amount.
  - Used explicit validation checks instead of relying on implicit type conversion.

- **Assumptions:**
  - Purchase and refund amounts are represented in paise.
  - Only valid captured purchases should earn reward points.
  - An event ID should be processed only once.
  - Refunds are cumulative and cannot exceed the original purchase amount.
  - Repeat transaction groups are flagged when their count is greater than the configured threshold.

## 5. Verification

- **Tests added or changed:**
  Added `tests/test_regressions.py` with seven regression tests:
  1. `test_negative_amount`
  2. `test_zero_cap`
  3. `test_duplicate_event`
  4. `test_refund_greater_than_purchase`
  5. `test_unknown_transaction_refund`
  6. `test_partial_refund`
  7. `test_empty_repeat_transactions`

- **Commands run and actual results:**
  - `python -m pip install -r requirements-dev.txt` — ran to install development dependencies.
  - `python -m pytest -q` — final result: **221 passed in 0.46s**.
  - `python -m main` — ran the main module.

- **Edge cases verified:**
  - Negative purchase amounts.
  - Zero reward point cap.
  - Duplicate event IDs.
  - Refunds greater than the original purchase.
  - Refunds for unknown transactions.
  - Partial refunds and proportional point reversal.
  - Empty repeat transaction input.

- **Remaining failures or known limitations:**
  - The final test run had no failing tests.
  - Refund behaviour when a customer has already spent some of their awarded points still needs a clearly defined business rule. The current implementation limits reversal to the available balance, so this scenario requires further consideration.
