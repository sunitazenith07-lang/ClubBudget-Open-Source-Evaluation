# REWARD_RULE_NOTES.md — Required submission

Complete this file with your own actual examples and results. Do not leave prompts unanswered.

## 1. Worked points calculation
Consider a purchase of **₹2,599.00** (`259900` paise) under rules:
- `points_per_100_rupees = 1`
- `bonus_percent = 10`
- `cap_points = 100`

### Step-by-step arithmetic:
1. **Base Points:**
   - Formula: `base_points = floor(amount_paise / 10000) * points_per_100_rupees`
   - Calculation: `259900 // 10000 = 25`. Then `25 * 1 = 25 base points`.
   - Rounding rule: Strictly integer floor division (discarding the fractional remainder of 99 paise).
2. **Promotional Bonus Points:**
   - Formula: `bonus_points = floor(base_points * (100 + bonus_percent) / 100)`
   - Calculation: `floor(25 * 110 / 100) = (25 * 110) // 100 = 2750 // 100 = 27 points`.
   - Rounding rule: Strictly integer floor division.
3. **Promotional Cap:**
   - Formula: `final_points = min(bonus_points, cap_points)` if `cap_points is not None` else `bonus_points`
   - Calculation: `min(27, 100) = 27 points`.
4. **Actual Output:**
   - `calculate_points(259900, 1, 10, 100) -> 27`

---

## 2. Partial-refund example
### Initial Purchase:
- Event: `purchase_captured`, `transaction_id = "TX-901"`, `amount_paise = 100000` (₹1,000.00).
- Rule: `points_per_100_rupees = 1`, `bonus_percent = 0`.
- Points awarded: `(100000 // 10000) * 1 = 10 points`.
- Account state: `points_balance = 10`, `transactions["TX-901"] = {amount_paise: 100000, awarded_points: 10, reversed_points: 0, refunded_paise: 0}`.
- Ledger entry: `{"event_id": "EV-1", "type": "purchase_captured", "points_delta": 10}`.

### Partial Refund:
- Event: `refund_processed`, `transaction_id = "TX-901"`, `amount_paise = 40000` (₹400.00).
- Validation: `40000 > 0`, `0 + 40000 <= 100000` -> Valid partial refund.
- Cumulative refunded paise: `0 + 40000 = 40000`.
- Target proportional points to reverse:
  - `should_reverse = (awarded_points * cumulative_refunded_paise) // amount_paise`
  - `should_reverse = (10 * 40000) // 100000 = 400000 // 100000 = 4 points`.
- Incremental reversal delta:
  - `delta = should_reverse - reversed_points = 4 - 0 = 4 points`.
  - Balance check: `min(delta, points_balance) = min(4, 10) = 4 points`.
- Resulting account state:
  - `points_balance = 10 - 4 = 6 points`.
  - `transactions["TX-901"]["reversed_points"] = 4`.
  - `transactions["TX-901"]["refunded_paise"] = 40000`.
- Relevant ledger entry written:
  - `{"event_id": "EV-2", "type": "refund_processed", "points_delta": -4}`.

---

## 3. Three edge cases
1. **Edge Case 1: Cap of Zero Points**
   - **Input:** `calculate_points(amount_paise=50000, points_per_100_rupees=1, bonus_percent=50, cap_points=0)`
   - **Expected behaviour:** A cap of zero indicates no points may be awarded. Return `0`.
   - **Actual observed result:** Returns `0`.
   - **Test verification:** `tests/test_contract.py::test_cap_zero_is_respected` and `tests/test_acceptance_matrix.py::test_bonus_and_cap_matrix[50000-2-50-0-0]`.
2. **Edge Case 2: Replay of Duplicate Event ID (Idempotency)**
   - **Input:** Process `apply_reward_event` with `event_id="PURCHASE-001"` twice sequentially on the same account.
   - **Expected behaviour:** The second invocation is a no-op; points balance is not incremented twice, no duplicate ledger entry is appended, and `processed_event_ids` contains exactly one instance of `"PURCHASE-001"`.
   - **Actual observed result:** Balance remains unchanged after second application; `len(account["ledger"]) == 1` and `account["processed_event_ids"] == ["PURCHASE-001"]`.
   - **Test verification:** `tests/test_acceptance_matrix.py::test_purchase_event_replay_is_idempotent[PURCHASE-001]`.
3. **Edge Case 3: Excess Refund Attempt (> 100% of Purchase)**
   - **Input:** A transaction of `100000` paise has already refunded `100000` paise. An additional refund event of `1` paise is processed.
   - **Expected behaviour:** The cumulative refund (`100001`) exceeds `amount_paise` (`100000`). The event must be rejected without mutating the account or ledger.
   - **Actual observed result:** Account state before and after the event are identical; no ledger entry is added and `refunded_paise` remains `100000`.
   - **Test verification:** `tests/test_regression.py::test_cumulative_multiple_partial_refunds`.

---

## 4. Assumptions and limitations
1. **Rounding Assumptions:**
   - All conversions from paise to rupees and all bonus calculations apply integer floor arithmetic (`//`). Fractional points are never generated or rounded up.
2. **Missing-Field Handling:**
   - Events with missing, empty, or non-string/non-int `event_id` or `transaction_id` are rejected immediately to preserve audit ledger and idempotency integrity.
   - Non-dictionary event or account inputs are handled gracefully without raising unhandled exceptions.
3. **Repeat-Alert Assumptions:**
   - Repeat alerts evaluate matching `(account_id, date, amount_paise)` groupings.
   - Alerts are triggered strictly when `len(transaction_ids) > threshold` (default `threshold=2`).
   - Alerts are advisory metadata for operations review and must never block transaction processing or alter account state.
4. **Unresolved Issues:**
   - None. All requirements and edge cases are verified by passing tests.
