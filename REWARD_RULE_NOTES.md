# REWARD_RULE_NOTES.md — Required submission

## 1. Worked points calculation
Example purchase:
- Purchase amount: Rs 2,599.00 = 259,900 paise
- Points rule: 1 point per Rs 100 (`points_per_100_rupees = 1`)
- Promotional bonus: 10% bonus (`bonus_percent = 10`)
- Cap: 100 points (`cap_points = 100`)

Step-by-step:
1. Complete Rs 100 units:
   `units = amount_paise // 10000 = 259900 // 10000 = 25`
   (The remaining 99.00 rupees / 9900 paise does not complete a full Rs 100 unit, so it earns 0 points.)
2. Base points:
   `base_points = 25 * 1 = 25 points`
3. Bonus points:
   `bonus_points = base_points * (100 + 10) // 100 = 25 * 110 // 100 = 2750 // 100 = 27 points`
   (27.5 truncated to 27 using integer floor division.)
4. Apply cap:
   `final_points = min(27, 100) = 27 points`

Actual output from `calculate_points(259900, 1, 10, 100)`: `27`
(The starter code previously returned 28 because `round(25.99)` rounded up to 26 units, which gave 28 points.)

---

## 2. Partial-refund example
Initial purchase:
- Purchase of Rs 1,000 (100,000 paise) earning 10 points.
- Account starts at 0 points balance.
- After purchase: `points_balance = 10`, `awarded_points = 10`, `reversed_points = 0`, `refunded_paise = 0`.
- Ledger entry: `{'event_id': 'E1', 'type': 'purchase_captured', 'points_delta': 10}`

First partial refund of Rs 300 (30,000 paise):
- Cumulative refunded paise becomes 30,000.
- Reversal needed: `(10 * 30000) // 100000 = 3 points`.
- Points delta: `3 - 0 = 3 points`.
- After refund: `points_balance = 7`, `reversed_points = 3`.
- Ledger entry: `{'event_id': 'E2', 'type': 'refund_processed', 'points_delta': -3}`

Second partial refund of Rs 700 (70,000 paise - completes 100% refund):
- Cumulative refunded paise becomes `30000 + 70000 = 100000`.
- Total reversal needed: `(10 * 100000) // 100000 = 10 points`.
- Points delta: `10 - 3 = 7 points`.
- After refund: `points_balance = 0`, `reversed_points = 10`.
- Ledger entry: `{'event_id': 'E3', 'type': 'refund_processed', 'points_delta': -7}`
- Total reversed points across both refunds: `3 + 7 = 10` points (all awarded points reversed).

---

## 3. Three edge cases
1. **Cap of zero (`cap_points = 0`)**
   - Input: `calculate_points(50000, 1, bonus_percent=50, cap_points=0)`
   - Expected: 0 points because cap is 0.
   - Actual result: 0 points.
   - Verified by: `test_contract.py::test_cap_zero_is_respected`
2. **Excess refund attempt**
   - Input: Purchase of 100,000 paise. Already refunded 60,000 paise. Then a refund event arrives for 50,000 paise (total 110,000 > 100,000).
   - Expected: Event is ignored, balance unchanged, refunded paise stays at 60,000.
   - Actual result: Ignored, balance unchanged.
   - Verified by: `test_regression.py::test_excess_refund_rejected_after_partial`
3. **Replaying an event**
   - Input: Submitting the same purchase event dictionary twice with `event_id = "PURCHASE-001"`.
   - Expected: Second call does nothing, balance is not added again, and no second ledger entry is written.
   - Actual result: `points_balance == 2`, `len(ledger) == 1`.
   - Verified by: `test_acceptance_matrix.py::test_purchase_event_replay_is_idempotent`

---

## 4. Assumptions and limitations
- Integer arithmetic: All calculations floor intermediate values using `//`. There are no fractional paise.
- Malformed inputs: Missing `event_id`, missing `transaction_id`, or negative amounts are ignored and do not change state.
- Python booleans: `True` and `False` are rejected because they are subclasses of `int` in Python and could otherwise be treated as numbers.
- Repeat alerts: Only groups with `count > threshold` are returned, sorted by `account_id`.
- In-memory limitations: State is kept in memory dicts without database locks, so concurrency in production would need external transaction management.
