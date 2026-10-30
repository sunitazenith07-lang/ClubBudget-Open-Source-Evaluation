# REWARD_RULE_NOTES.md — Required submission

## 1. Worked points calculation
Using the sample purchase and rule from `fixtures.py` and `main.py`:
- **Inputs**:
  - `amount_paise = 259900` (Rs. 2,599.00)
  - `points_per_100_rupees = 1`
  - `bonus_percent = 10`
  - `cap_points = 100`
- **Step 1 - Base points (floor division by 10,000 paise = Rs. 100)**:
  - Formula: `base_points = floor(amount_paise / 10000) * points_per_100_rupees`
  - Calculation: `(259900 // 10000) * 1 = 25 * 1 = 25`
  - Rounding rule: Integer floor division (`//`). The extra `9900` paise (Rs. 99) is dropped, not rounded up.
- **Step 2 - Bonus points (floor division)**:
  - Formula: `bonus_points = floor(base_points * (100 + bonus_percent) / 100)`
  - Calculation: `(25 * (100 + 10)) // 100 = 2750 // 100 = 27`
  - Rounding rule: Integer floor division (`//`). `27.5` floors down to `27`.
- **Step 3 - Cap applied last**:
  - Formula: `final_points = min(bonus_points, cap_points)`
  - Calculation: `min(27, 100) = 27`
- **Actual output** (from `py -m main`):
  ```text
  Points example: 27
  Repeat warnings: []
  ```

## 2. Partial-refund example
- **Original purchase (`event_id="E1"`, `transaction_id="T1"`)**:
  - Purchase `amount_paise = 100000` (Rs. 1,000.00) with `rules = {"points_per_100_rupees": 1, "bonus_percent": 0, "cap_points": None}`.
  - Points originally awarded: `10` (`points_balance = 10`).
  - Ledger entry added: `{"event_id": "E1", "type": "purchase_captured", "points_delta": 10}`.
- **First partial refund (`event_id="E2"`, `transaction_id="T1"`, `amount_paise=30000`)**:
  - Refund amount: `30000` paise; cumulative `refunded_paise = 30000`.
  - Reversal calculation:
    - `should_reverse = (awarded_points * refunded_paise) // amount_paise = (10 * 30000) // 100000 = 3`
    - `delta = should_reverse - reversed_points = 3 - 0 = 3`
  - Resulting balance: `points_balance = 10 - 3 = 7` (`reversed_points = 3`).
  - Ledger entry added: `{"event_id": "E2", "type": "refund_processed", "points_delta": -3}`.
- **Second partial refund (`event_id="E3"`, `transaction_id="T1"`, `amount_paise=20000`)**:
  - Refund amount: `20000` paise; cumulative `refunded_paise = 30000 + 20000 = 50000`.
  - Reversal calculation:
    - `should_reverse = (10 * 50000) // 100000 = 5`
    - `delta = 5 - 3 = 2`
  - Resulting balance: `points_balance = 7 - 2 = 5` (`reversed_points = 5`).
  - Ledger entry added: `{"event_id": "E3", "type": "refund_processed", "points_delta": -2}`.

## 3. Three edge cases
1. **Zero points cap (`cap_points = 0`)**:
   - Input: `calculate_points(50000, 2, bonus_percent=50, cap_points=0)`
   - Expected behaviour: Returns `0` because a cap of `0` means no points can be awarded.
   - Actual observed result: `0`
   - Test that verifies it: `tests/test_contract.py::test_cap_zero_is_respected`
2. **Boolean refund amount (`amount_paise = True`)**:
   - Input: `apply_reward_event(account_with_10_pts, {"event_id": "R", "type": "refund_processed", "transaction_id": "T", "amount_paise": True}, {"points_per_100_rupees": 1})`
   - Expected behaviour: Ignored without changing `refunded_paise` (`0`) or `points_balance` (`10`), even though `isinstance(True, int)` is `True` in Python.
   - Actual observed result: `result["transactions"]["T"]["refunded_paise"] == 0` and `result["points_balance"] == 10`
   - Test that verifies it: `tests/test_acceptance_matrix.py::test_invalid_or_excess_refund_does_not_change_account[True]`
3. **Cumulative partial refunds, duplicate event replay, and 1-paisa excess refund**:
   - Input: Purchase `T1` of `100000` paise (`10` points), followed by partial refund `E2` (`30000` paise), duplicate replay of `E2` (`30000` paise), second partial refund `E3` (`70000` paise), and excess refund `E4` (`1` paisa).
   - Expected behaviour: `E2` reverses `3` points (balance `7`), the replay of `E2` is ignored, `E3` reverses `7` points (`refunded_paise == 100000`, `points_balance == 0`), and `E4` (`100001 > 100000`) is ignored.
   - Actual observed result: `points_balance == 0`, `refunded_paise == 100000`, `reversed_points == 10`, `len(ledger) == 3`
   - Test that verifies it: `tests/test_contract.py::test_refund_event_replay_and_cumulative_partial_refunds`

## 4. Assumptions and limitations
- **Rounding assumptions**: Base points, bonus points, and refund reversals all use integer floor division (`//`).
- **Missing-field handling**: Events missing a valid string `event_id` or `transaction_id`, or having non-integer/negative/zero `amount_paise`, are ignored and not added to `processed_event_ids` or `ledger`.
- **Repeat-alert threshold assumptions**: Transactions are grouped by `(account_id, date, amount_paise)`. Only `"CAPTURED"` transactions are counted when `status` is present, duplicate `transaction_id`s are counted once, and an alert is returned when `len(transaction_ids) > threshold` (for `threshold >= 1`).
- **Unresolved issues**: None (`218 passed`). All state is kept in memory per account dict.
