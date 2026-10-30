# REWARD_RULE_NOTES.md — Required submission

Complete this file with your own actual examples and results. Do not leave prompts unanswered.

## 1. Worked points calculation
Show one purchase calculation from amount in paise through base points, bonus and cap. State the rounding rule at each step and include the actual output.

- **Input:**
  - `amount_paise = 259900` (₹2,599.00)
  - `points_per_100_rupees = 1`
  - `bonus_percent = 10`
  - `cap_points = 100`

- **Step 1: Base Points Calculation**
  - Formula: `floor(amount_paise / 10000) * points_per_100_rupees`
  - Computation: `floor(259900 / 10000) * 1 = 25 * 1 = 25`
  - Rounding rule: Truncation via integer floor division (`//`). The remaining 9900 paise (₹99.00) do not earn points as they do not constitute a full 100 rupees.

- **Step 2: Bonus Points Calculation**
  - Formula: `floor(base_points * (100 + bonus_percent) / 100)`
  - Computation: `floor(25 * (100 + 10) / 100) = floor(2750 / 100) = 27`
  - Rounding rule: Integer floor division (`//`). 2750 // 100 = 27 points.

- **Step 3: Cap Application**
  - Formula: `min(points, cap_points)` if `cap_points is not None`
  - Computation: `min(27, 100) = 27`
  - Final Output: `27 points` (previously erroneous starter returned 28 due to floating `round()`).

## 2. Partial-refund example
Show the points originally awarded, the refund amount, how the reversal is calculated, the resulting balance, and the relevant ledger entry.

- **Initial Purchase (`purchase_captured`):**
  - `amount_paise = 100000` (₹1,000.00)
  - `awarded_points = 10`
  - Initial `points_balance = 10`
  - Initial `transactions['T'] = {'amount_paise': 100000, 'awarded_points': 10, 'reversed_points': 0, 'refunded_paise': 0}`

- **Partial Refund Event (`refund_processed`):**
  - `amount_paise = 50000` (₹500.00, a 50% refund)
  - `new_refunded_paise = txn['refunded_paise'] + 50000 = 50000`
  - `should_reverse = floor(txn['awarded_points'] * new_refunded_paise / txn['amount_paise'])`
    `= floor(10 * 50000 / 100000) = 5 points`
  - `delta = should_reverse - txn['reversed_points'] = 5 - 0 = 5 points`
  - New `points_balance = 10 - 5 = 5 points`
  - Updated transaction record: `reversed_points = 5`, `refunded_paise = 50000`
  - Ledger Entry Appended:
    `{'event_id': 'E2', 'type': 'refund_processed', 'points_delta': -5}`

## 3. Three edge cases
For each, provide input, expected behaviour, actual observed result, and the test that verifies it.

1. **Cap of Zero (`cap_points = 0`)**
   - **Input:** `calculate_points(50000, 1, bonus_percent=50, cap_points=0)`
   - **Expected behaviour:** Strict cap of 0 points means exactly 0 points are awarded, even if base and bonus would have produced points.
   - **Actual observed result:** `0`
   - **Test:** `test_contract.py::test_cap_zero_is_respected` and `test_acceptance_matrix.py::test_bonus_and_cap_matrix[50000-2-50-0-0]`

2. **Replayed Purchase and Refund Events (Idempotency)**
   - **Input:** Re-submitting an already processed event `event_id = "PURCHASE-001"` or `event_id = "REFUND-001"`.
   - **Expected behaviour:** Account state remains unchanged. No duplicate points awarded/deducted, no duplicate ledger records, and `processed_event_ids` does not append duplicate event IDs.
   - **Actual observed result:** Account untouched on replay; exactly 1 ledger record; 1 unique event ID recorded.
   - **Test:** `test_contract.py::test_purchase_event_once` and `test_regression.py::TestApplyRewardEventRegression::test_refund_event_idempotency`

3. **Excess Refund Beyond Original Purchase Amount**
   - **Input:** Purchase for 100000 paise (10 points awarded), followed by a refund event for 150000 paise (or negative / non-integer amount).
   - **Expected behaviour:** The excess refund is invalid and safely rejected without altering `refunded_paise`, `reversed_points`, or `points_balance`.
   - **Actual observed result:** `refunded_paise` remains 0 and `points_balance` remains 10.
   - **Test:** `test_contract.py::test_invalid_or_excess_refund_ignored` and `test_regression.py::TestApplyRewardEventRegression::test_cumulative_partial_refunds_and_over_refund`

## 4. Assumptions and limitations
Document rounding assumptions, missing-field handling, repeat-alert threshold assumptions, and any unresolved issue.

- **Rounding Assumptions:** Points are strictly non-negative integers. All division operations (`amount // 10000`, `bonus // 100`, proportional refund calculations) use integer floor division without intermediate float conversions to prevent floating-point inaccuracies.
- **Missing or Invalid Fields:** Events missing `event_id`, missing `transaction_id`, or having non-string/non-integer amounts (including boolean values like `True`/`False` which inherit from `int`) are considered invalid and discarded without mutating account state.
- **Repeat Alert Threshold:** The threshold defines the strict upper limit of unflagged identical transactions. Groups are only flagged when `count > threshold`. Alerts are informational review objects only and never block processing or alter financial balances.
- **Unresolved issues:** None. All contract tests, acceptance matrices, and edge-case regression suites pass cleanly with 100% compliance.
