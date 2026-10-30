# REWARD_RULE_NOTES.md — Required submission

Complete this file with your own actual examples and results. Do not leave prompts unanswered.

## 1. Worked points calculation
Consider a purchase transaction from the offline demonstration:
- **Transaction Input:**
  - `amount_paise = 259900` (equivalent to ₹2,599.00)
  - `points_per_100_rupees = 1`
  - `bonus_percent = 10` (promotional 10% bonus)
  - `cap_points = 100`

- **Step 1: Base Points Calculation**
  - Formula: `base_points = (amount_paise // 10000) * points_per_100_rupees`
  - Computation: `259900 // 10000 = 25` hundred-rupee units; `25 * 1 = 25` base points.
  - *Rounding Rule:* Strict integer floor division (`// 10000`). The sub-100 rupee fraction of 9,900 paise (₹99.00) is truncated and earns 0 points.
  - *Intermediate Output:* `25` base points.

- **Step 2: Promotional Bonus Calculation**
  - Formula: `bonus_points = (base_points * (100 + bonus_percent)) // 100`
  - Computation: `(25 * (100 + 10)) // 100 = (25 * 110) // 100 = 2750 // 100 = 27` points.
  - *Rounding Rule:* Strict integer floor division (`// 100`). The 0.5 fractional bonus point is truncated to 0.
  - *Intermediate Output:* `27` points.

- **Step 3: Cap Points Application**
  - Formula: `final_points = min(bonus_points, cap_points)` if `cap_points is not None` else `bonus_points`
  - Computation: `min(27, 100) = 27` points.
  - *Rounding Rule:* Capped at maximum allowed threshold; when below cap, points remain unchanged.
  - *Actual Output:* **27 points** (The starter code incorrectly produced 28 because `round(25.99)` rounded up to 26).

---

## 2. Partial-refund example
Consider the same purchase receiving a subsequent partial refund:
- **Original Award State:**
  - `transaction_id = "TX-1001"`
  - `amount_paise = 259900`
  - `awarded_points = 27`
  - Initial `points_balance = 27`
  - `reversed_points = 0`, `refunded_paise = 0`

- **Refund Event Details:**
  - `event_id = "EVT-002"`
  - `type = "refund_processed"`
  - `transaction_id = "TX-1001"`
  - `amount_paise = 100000` (₹1,000.00 partial refund)

- **Proportional Reversal Calculation:**
  - Cumulative refunded paise: `new_refunded_paise = 0 + 100000 = 100000` (validated $\le 259900$)
  - Points to reverse to date:
    $$\text{should\_reverse} = \left\lfloor \frac{\text{awarded\_points} \times \text{new\_refunded\_paise}}{\text{amount\_paise}} \right\rfloor = \left\lfloor \frac{27 \times 100000}{259900} \right\rfloor = \left\lfloor \frac{2700000}{259900} \right\rfloor = 10 \text{ points}$$
  - Incremental reversal delta: `delta = should_reverse - reversed_points = 10 - 0 = 10` points.
  - Clamping check: `delta` $\le$ current `points_balance` ($10 \le 27$) and $\le$ `awarded_points` ($10 \le 27$).

- **Resulting Account & Transaction State:**
  - Updated Account `points_balance`: `27 - 10 = 17` points.
  - Updated Transaction Record:
    ```python
    {
        'amount_paise': 259900,
        'awarded_points': 27,
        'reversed_points': 10,
        'refunded_paise': 100000
    }
    ```
  - Appended Audit Ledger Entry:
    ```python
    {
        'event_id': 'EVT-002',
        'type': 'refund_processed',
        'points_delta': -10
    }
    ```

---

## 3. Three edge cases

### Edge Case 1: Cap Points Set to Exactly Zero
- **Input:** `amount_paise = 50000`, `points_per_100_rupees = 2`, `bonus_percent = 50`, `cap_points = 0`.
- **Expected Behaviour:** Base points = 10, bonus points = 15. The rule explicitly specifies a cap of zero (`cap_points = 0`), which means zero points must be awarded.
- **Actual Observed Result:** `0` points awarded.
- **Verifying Test:** `tests/test_contract.py::test_cap_zero_is_respected` and `tests/test_acceptance_matrix.py::test_bonus_and_cap_matrix[50000-2-50-0-0]`.

### Edge Case 2: Excess Refund Exceeding Original Purchase Amount
- **Input:** Account has captured purchase of `100000` paise (10 points awarded). An incoming refund event requests `amount_paise = 150000`.
- **Expected Behaviour:** Since `150000 > 100000`, the refund is invalid (exceeds total purchase). The event must be rejected without mutating account balance, without updating `refunded_paise`, and without creating a ledger entry.
- **Actual Observed Result:** Account `points_balance` remains `10`, `transactions['T']['refunded_paise']` remains `0`, and no ledger entry is created.
- **Verifying Test:** `tests/test_contract.py::test_invalid_or_excess_refund_ignored` and `tests/test_acceptance_matrix.py::test_invalid_or_excess_refund_does_not_change_account[150000]`.

### Edge Case 3: Replay of Processed Refund Event (Idempotency)
- **Input:** Account with purchase of `100000` paise (10 points awarded) has refund event `{"event_id": "R-1", "type": "refund_processed", "amount_paise": 50000}` applied. The exact same event `R-1` is re-sent.
- **Expected Behaviour:** The system detects `R-1` in `processed_event_ids` and returns the account unmodified. The balance remains 5 points, reversed points remains 5, and the ledger retains exactly 2 entries total.
- **Actual Observed Result:** Balance remains `5`, `processed_event_ids` remains `["P-1", "R-1"]`, and ledger length remains 2.
- **Verifying Test:** `tests/test_regression.py::test_refund_event_replay_is_idempotent`.

---

## 4. Assumptions and limitations
- **Rounding Assumptions:**
  All currency divisions and fractional points conversions use mathematical integer floor truncation (`//`). Fractional paise and fractional points never carry over between transactions or round upwards.
- **Missing-Field & Malformed Input Handling:**
  Events lacking required identifiers (`event_id` or `transaction_id`), non-string identifiers, or non-numeric/negative amounts are treated as malformed and safely ignored without raising unhandled exceptions or corrupting account state.
- **Repeat-Alert Threshold Assumptions:**
  Alerts are flagged strictly when the count of transactions sharing the composite key `(account_id, date, amount_paise)` strictly exceeds `threshold` (`len(ids) > threshold`). Alerts are purely informational for compliance review and do not block or reject transactions.
- **Concurrency & Ledger Storage Limitations:**
  The current implementation manages accounts as in-memory Python dictionaries. In a distributed multi-instance environment, optimistic locking, idempotent message queues (e.g., Kafka with deduplication keys), and persistent ACID databases are required to manage high-throughput concurrent transactions.
