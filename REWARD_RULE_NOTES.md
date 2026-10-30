# REWARD_RULE_NOTES.md — Required submission

## 1. Worked points calculation

### Transaction Details
- **Purchase amount**: `259,900 paise` (₹2,599.00)
- **Rules applied**:
  - `points_per_100_rupees`: `1`
  - `bonus_percent`: `10` (10% bonus)
  - `cap_points`: `100`

### Step-by-Step Calculation
1. **Base Points Calculation**:
   $$\text{base\_points} = \lfloor \frac{\text{amount\_paise}}{10000} \rfloor \times \text{points\_per\_100\_rupees}$$
   $$\text{base\_points} = \lfloor \frac{259900}{10000} \rfloor \times 1 = 25 \times 1 = 25\text{ points}$$
   *Rounding Rule*: Integer floor division (`259900 // 10000`). The fractional 9,900 paise (₹99.00) is below the 100-rupee earning threshold and is strictly discarded.

2. **Bonus Points Calculation**:
   $$\text{bonus\_points} = \lfloor \frac{\text{base\_points} \times (100 + \text{bonus\_percent})}{100} \rfloor$$
   $$\text{bonus\_points} = \lfloor \frac{25 \times 110}{100} \rfloor = \lfloor \frac{2750}{100} \rfloor = 27\text{ points}$$
   *Rounding Rule*: Integer floor division (`2750 // 100`). The 0.5 fractional point (50/100) is discarded.

3. **Promotional Cap Application**:
   $$\text{points} = \min(\text{bonus\_points}, \text{cap\_points}) = \min(27, 100) = 27\text{ points}$$
   *Rule*: Since 27 is below the cap of 100 points, the earned points remain 27.

- **Actual output**: `27`
*(Note: The starter codebase outputted 28 due to using `round(25.99)` which improperly rounded up to 26 base points; our integer floor fix accurately outputs 27).*

---

## 2. Partial-refund example

### Scenario
A customer makes a captured purchase and later receives a 50% partial refund.
- **Original purchase amount**: `100,000 paise` (₹1,000.00)
- **Rules**: `points_per_100_rupees = 1`, `bonus_percent = 0`, `cap_points = None`
- **Points originally awarded**: `10 points`
- **Initial Account Balance**: `10 points`
- **Initial Ledger**:
  ```json
  [
    {"event_id": "EVT-P10", "type": "purchase_captured", "points_delta": 10}
  ]
  ```

### Refund Event Processing
- **Refund amount**: `50,000 paise` (₹500.00)
- **Validation**:
  - `50,000` is a positive integer.
  - Previous refunded paise was `0`. `0 + 50,000 <= 100,000`, so the refund is within bounds.
- **Reversal Calculation**:
  $$\text{should\_reverse} = \lfloor \frac{\text{awarded\_points} \times \text{cumulative\_refunded\_paise}}{\text{amount\_paise}} \rfloor$$
  $$\text{should\_reverse} = \lfloor \frac{10 \times 50000}{100000} \rfloor = \lfloor \frac{500000}{100000} \rfloor = 5\text{ points}$$
  $$\text{delta} = \text{should\_reverse} - \text{reversed\_points} = 5 - 0 = 5\text{ points}$$
- **Balance Update**:
  $$\text{new\_balance} = \text{points\_balance} - \text{delta} = 10 - 5 = 5\text{ points}$$
- **Transaction State Update**:
  - `refunded_paise`: `50,000`
  - `reversed_points`: `5`
- **Ledger Entry Appended**:
  ```json
  {"event_id": "EVT-R10", "type": "refund_processed", "points_delta": -5}
  ```

---

## 3. Three edge cases

### Edge Case 1: Purchase immediately below 100-rupee boundary
- **Input**: `amount_paise = 9999` (₹99.99), `points_per_100_rupees = 1`
- **Expected behaviour**: Base points must be strictly 0 because integer floor division `9999 // 10000` equals 0. No points should be awarded.
- **Actual observed result**: `0` points awarded. (The starter code incorrectly awarded 1 point via `round(0.9999)`).
- **Test verifying it**: `test_integer_floor_points_calculation[9999-0_0]` in `tests/test_acceptance_matrix.py`.

### Edge Case 2: Promotional cap set to zero
- **Input**: `amount_paise = 50000` (₹500.00), `points_per_100_rupees = 1`, `cap_points = 0`
- **Expected behaviour**: A cap of zero points must strictly yield zero points, overriding any calculated base or bonus points.
- **Actual observed result**: `0` points awarded. (The starter code awarded 5 points because `if cap_points:` treated 0 as falsy and skipped the cap check).
- **Test verifying it**: `test_cap_zero_is_respected` in `tests/test_contract.py`.

### Edge Case 3: Replaying an already-processed refund event (Idempotency)
- **Input**: Refund event `{"event_id": "EVT-R1", "type": "refund_processed", "transaction_id": "TX-1", "amount_paise": 40000}` applied a second time to an account where it was already processed.
- **Expected behaviour**: The second application must be a no-op: points balance remains unchanged, no duplicate entries are appended to the ledger, and `processed_event_ids` remains unchanged.
- **Actual observed result**: Account state is returned completely unmodified (`points_balance` remained 6, ledger length remained 2, `processed_event_ids` contained single `EVT-R1`).
- **Test verifying it**: `test_refund_event_replay_is_idempotent` in `tests/test_regression_and_edge_cases.py`.

---

## 4. Assumptions and limitations
1. **Rounding Assumptions**:
   - Integer floor arithmetic (`//`) is strictly applied at every stage (base calculation, bonus application, and refund reversal). No intermediate fractional points are banked across transactions.
2. **Missing and Malformed Fields**:
   - Any event missing `event_id`, `type`, or `transaction_id` is rejected safely without modifying the account balance or ledger.
   - Non-integer types (`bool`, `None`, strings, floats, collections) passed as amounts or rule values are safely treated as invalid and produce 0 points.
3. **Refund Limits**:
   - A transaction cannot be refunded for more than its captured purchase amount (`txn['refunded_paise'] + refund <= txn['amount_paise']`).
   - Over-refund attempts are rejected entirely rather than partially applied.
4. **Negative Balance Safeguard**:
   - Points reversals cannot drive an account balance below zero (`delta = min(delta, out['points_balance'])`).
5. **Repeat Alerts**:
   - Alerts group transactions strictly by identical `(account_id, date, amount_paise)` tuples where the number of matching transactions strictly exceeds `threshold`.
   - Alerts are advisory markers for human operations review and do not alter transaction processing or customer account state.
