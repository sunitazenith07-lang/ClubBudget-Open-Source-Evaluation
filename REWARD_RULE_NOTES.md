# REWARD_RULE_NOTES.md — Required submission

Complete this file with your own actual examples and results. Do not leave prompts unanswered.

## 1. Worked points calculation
Show one purchase calculation from amount in paise through base points, bonus and cap. State the rounding rule at each step and include the actual output.

### Example Scenario
- Purchase amount: `259,900 paise` (INR 2,599.00)
- Rule parameters:
  - `points_per_100_rupees = 1`
  - `bonus_percent = 10`
  - `cap_points = 100`

### Step-by-Step Calculation
1. **Base Points Calculation:**
   - Formula: `base_points = (amount_paise // 10000) * points_per_100_rupees`
   - Calculation: `259900 // 10000 = 25` (integer floor division truncating paise below full 100 Rupees).
   - Base points: `25 * 1 = 25`.
   - Rounding rule: Strictly integer floor division (`// 10000`). No half-up rounding or ceiling.

2. **Bonus Points Calculation:**
   - Formula: `bonus_points = base_points * (100 + bonus_percent) // 100`
   - Calculation: `25 * (100 + 10) // 100 = 25 * 110 // 100 = 2750 // 100 = 27`.
   - Rounding rule: Strictly integer floor division (`// 100`). Truncates fractional bonus points.

3. **Cap Application:**
   - Formula: `points = min(bonus_points, cap_points)` (since `cap_points` is not None).
   - Calculation: `min(27, 100) = 27`.
   - Rounding rule: Direct minimum comparison with non-negative bounds check (`max(0, points)`).

### Output
- `calculate_points(259900, 1, 10, 100) -> 27`
- *Note:* The starter code previously output `28` because it used `round(259900 / 10000) -> 26`, which incorrectly rounded up paise on boundary amounts. The corrected integer floor arithmetic yields the correct `27` points.

---

## 2. Partial-refund example
Show the points originally awarded, the refund amount, how the reversal is calculated, the resulting balance, and the relevant ledger entry.

### Original Purchase Event
- Event: `{'event_id': 'E-PURCHASE-1', 'type': 'purchase_captured', 'transaction_id': 'TX-100', 'amount_paise': 100000}`
- Rules: `{'points_per_100_rupees': 1, 'bonus_percent': 50}` (Base: 10, Bonus: 5 -> Total 15 points awarded).
- Points Awarded: `15`
- Account State:
  - `points_balance`: `15`
  - `transactions['TX-100']`: `{'amount_paise': 100000, 'awarded_points': 15, 'reversed_points': 0, 'refunded_paise': 0}`
  - Ledger: `[{'event_id': 'E-PURCHASE-1', 'type': 'purchase_captured', 'points_delta': 15}]`

### Partial Refund 1 (50% Refund)
- Event: `{'event_id': 'E-REFUND-1', 'type': 'refund_processed', 'transaction_id': 'TX-100', 'amount_paise': 50000}`
- Calculation:
  - `new_refunded = 0 + 50000 = 50000`
  - `should_reverse = (awarded_points * new_refunded) // amount_paise = (15 * 50000) // 100000 = 750000 // 100000 = 7`
  - `delta = should_reverse - reversed_points = 7 - 0 = 7`
  - `points_balance = 15 - 7 = 8`
- Updated State:
  - `points_balance`: `8`
  - `transactions['TX-100']`: `{'amount_paise': 100000, 'awarded_points': 15, 'reversed_points': 7, 'refunded_paise': 50000}`
  - Ledger append: `{'event_id': 'E-REFUND-1', 'type': 'refund_processed', 'points_delta': -7}`

### Partial Refund 2 (Remaining 50% Refund)
- Event: `{'event_id': 'E-REFUND-2', 'type': 'refund_processed', 'transaction_id': 'TX-100', 'amount_paise': 50000}`
- Calculation:
  - `new_refunded = 50000 + 50000 = 100000` (Cumulative 100%)
  - `should_reverse = (15 * 100000) // 100000 = 15`
  - `delta = should_reverse - reversed_points = 15 - 7 = 8`
  - `points_balance = 8 - 8 = 0`
- Updated State:
  - `points_balance`: `0`
  - `transactions['TX-100']`: `{'amount_paise': 100000, 'awarded_points': 15, 'reversed_points': 15, 'refunded_paise': 100000}`
  - Ledger append: `{'event_id': 'E-REFUND-2', 'type': 'refund_processed', 'points_delta': -8}`
- *Result:* Total points reversed = `7 + 8 = 15`, exactly matching total awarded points with zero drift.

---

## 3. Three edge cases
For each, provide input, expected behaviour, actual observed result, and the test that verifies it.

### Edge Case 1: Zero Cap Enforcement (`cap_points = 0`)
- **Input:** `calculate_points(amount_paise=50000, points_per_100_rupees=1, bonus_percent=50, cap_points=0)`
- **Expected behaviour:** A cap of zero means zero points awarded.
- **Actual observed result:** Returned `0` points. (Starter previously returned `7` because `if cap_points:` treated `0` as falsy).
- **Test:** `tests/test_contract.py::test_cap_zero_is_respected` and `tests/test_acceptance_matrix.py::test_bonus_and_cap_matrix[50000-2-50-0-0]`.

### Edge Case 2: Purchase and Refund Event Replay Idempotency
- **Input:** Replaying `apply_reward_event` with identical `event_id` (`E1`) for `purchase_captured` or `refund_processed`.
- **Expected behaviour:** Idempotent no-op on replayed event; `points_balance` unchanged, no duplicate transaction or ledger entries, `processed_event_ids` preserves deduplicated record.
- **Actual observed result:** Account returned completely unchanged; `points_balance == 2`, `len(ledger) == 1`, `processed_event_ids == ['E1']`.
- **Test:** `tests/test_contract.py::test_purchase_event_once` and `tests/test_regression.py::test_refund_replay_is_idempotent`.

### Edge Case 3: Invalid and Cumulative Over-Refund Rejection
- **Input:** Purchase of 100,000 paise (10 points awarded), followed by refund events with amounts `-1`, `0`, or `150000` (exceeding original 100,000 paise).
- **Expected behaviour:** All invalid, non-positive, or excess refunds must be rejected without altering account state, ledger, or transaction refund totals.
- **Actual observed result:** Account remained unchanged; `refunded_paise == 0`, `points_balance == 10`, no ledger append.
- **Test:** `tests/test_contract.py::test_invalid_or_excess_refund_ignored` and `tests/test_acceptance_matrix.py::test_invalid_or_excess_refund_does_not_change_account`.

---

## 4. Assumptions and limitations
- **Integer arithmetic:** All monetary and points computations strictly avoid floating-point representation (`//` integer floor used throughout). Fractions of 100 rupees earn zero points.
- **Cumulative tracking for refunds:** Refund reversal calculates total required reversal from cumulative refunded paise rather than multiplying incremental refund amounts. This ensures mathematical convergence (total reversed == total awarded upon 100% refund).
- **Non-negative points balance:** The points balance is strictly prohibited from dropping below 0. In edge situations where reversals exceed current account balance, the delta deducted is clamped to available points.
- **Missing and malformed fields:** Missing or non-string `event_id`, missing `transaction_id`, non-dictionary payloads, and boolean types for numeric parameters are safely rejected without throwing unhandled exceptions.
- **Human-review alerts:** Repeat alerts based on matching `(account_id, date, amount_paise)` above a configurable threshold are purely informational for operational review and do not block transaction processing.

