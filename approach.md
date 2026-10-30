# approach.md - Required submission

## 1. Baseline
- **Commands run before editing:**
  - `python -m pip install -r requirements-dev.txt`
  - `python -m pytest -q`
  - `python -m main`
- **Initial test result (actual summary):**
  - `67 failed, 147 passed in 1.37s` on Python 3.14.7.
- **Demo/output observed:**
  ```text
  Points example: 28
  Repeat warnings: []
  ```
  Note: `Points example: 28` revealed a rounding defect where 259,900 paise (2,599 Rs) at 10% bonus calculated 28 points instead of 27 due to `round()` rounding 25.99 up to 26 instead of using integer floor division.

## 2. Codebase understanding
- **Important files/functions inspected:**
  - `service.py`: Contains `calculate_points()`, `apply_reward_event()`, and `flag_repeat_transactions()`.
  - `models.py`: Defines the initial state structure via `new_account(account_id)`.
  - `fixtures.py` & `main.py`: Setup rules and mock transactions for offline verification.
  - `data/records.json` & `data/README.txt`: 40 accounts, 180 repeat records, 264 reward events, and 8 rule configurations.
  - `tests/test_contract.py` & `tests/test_acceptance_matrix.py`: Contract tests covering boundaries, rules, idempotency, refund limits, and grouping logic.
- **Rewards calculation, refund, ledger or alert flow traced:**
  - *Purchase flow*: Input amount in paise -> floor divide by 10000 -> multiply by points per 100 rupees -> calculate bonus percent -> clamp by optional cap -> add transaction record to account -> update running balance -> append positive points delta to audit ledger -> track `event_id`.
  - *Refund flow*: Check transaction exists -> validate refund amount (must be positive int, <= remaining unrefunded paise) -> calculate cumulative proportional reversal via integer arithmetic -> clamp delta to remaining balance and awarded points -> deduct from running balance -> append negative points delta to audit ledger -> track `event_id`.
  - *Repeat alert flow*: Group transactions by `(account_id, date, amount_paise)` tuple -> filter groups where transaction count exceeds `threshold` -> return deterministic list ordered by group key.
- **How I confirmed my understanding:**
  - Traced unit test assertions in `tests/test_contract.py` against the problem statement specification.
  - Tested edge values (amounts ending in 9999 paise, negative rules, zero caps, duplicate event replays) manually in interactive Python.

## 3. Investigation and implementation strategy

### Issue 1: Floating-Point Rounding Instead of Integer Floor Division
- **Symptom**: `test_integer_floor_points_calculation` failed for multiple boundary amounts (e.g. 9999 paise awarded 1 point instead of 0; 19999 paise awarded 2 points instead of 1; 259900 paise gave 28 points in `main.py`).
- **Hypothesis**: The starter implementation in `service.py` was computing `base = round(amount_paise / 10000) * points_per_100_rupees`. The problem specification explicitly mandates integer arithmetic (`base_points = floor(amount_paise / 10000)`).
- **Evidence**: `calculate_points(19999, 1)` returned `2` because `19999 / 10000 = 1.9999`, which `round()` rounds to `2`.
- **Fix**: Replaced floating-point division and rounding with Python integer floor division:
  ```python
  base_points = (amount_paise // 10000) * points_per_100_rupees
  points = (base_points * (100 + bonus_percent)) // 100
  ```

### Issue 2: Event Replay Idempotency Defect
- **Symptom**: `test_purchase_event_replay_is_idempotent` failed for all test cases (`PURCHASE-000` to `PURCHASE-019`).
- **Hypothesis**: The starter function `apply_reward_event()` did not check if `event_id` was already in `out['processed_event_ids']` before appending it and processing.
- **Evidence**: On a second call with the same `event_id`, `out['processed_event_ids']` contained duplicates (`['E1', 'E1']`) and the ledger had duplicate entries.
- **Fix**: Added an early idempotency guard:
  ```python
  if event_id in out["processed_event_ids"]:
      return out
  ```
  Only append `event_id` to `processed_event_ids` when the event is accepted.

### Issue 3: Missing Validation on Refund Bounds and Excess Refunds
- **Symptom**: `test_refund_amount_bounds_and_balance` and `test_invalid_or_excess_refund_does_not_change_account` failed for negative values, excess amounts (> purchase), and non-integer types (`True`, `None`, `"100"`, `1.5`, `[]`, `{}`).
- **Hypothesis**: The starter code blindly added `txn['refunded_paise'] += refund` without validating the type, positivity, or comparison with `txn['amount_paise']`.
- **Evidence**: Passing `-1` or `150000` on a `100000` paise purchase mutated `txn['refunded_paise']` and generated negative or excess ledger deltas.
- **Fix**: Added type and bounds checking:
  ```python
  if isinstance(refund, bool) or not isinstance(refund, int) or refund <= 0:
      return out
  if txn["refunded_paise"] + refund > txn["amount_paise"]:
      return out
  ```
  Safeguarded proportional reversal with integer division and ensured delta does not exceed `out['points_balance']` or `txn['awarded_points']`.

### Issue 4: Cap Points Zero Value Ignored
- **Symptom**: `test_cap_zero_is_respected` failed (`calculate_points(50000, 1, cap_points=0)` returned 5 instead of 0).
- **Hypothesis**: The starter check `if cap_points:` treats `0` as falsy in Python, bypassing the cap logic when `cap_points == 0`.
- **Evidence**: `bool(0)` is `False`, skipping `points = min(points, cap_points)`.
- **Fix**: Changed the condition to `if cap_points is not None:` and explicitly handled `cap_points == 0` returning `0`.

## 4. Implementation decisions
- **Main changes and why:**
  - Implemented strict integer arithmetic across points calculations and refund reversals to avoid IEEE-754 precision issues in financial loyalty math.
  - Implemented defensive type checks (specifically filtering out `bool`, which inherits from `int` in Python) to prevent malformed inputs from altering account state.
  - Ensured idempotency at the event level to guarantee that replaying webhook events does not duplicate ledger entries or points balances.
  - Implemented `generate_account_statement_csv()` as optional stretch work to export the audit ledger to CSV.
- **Alternatives considered and why rejected:**
  - *Floating-point math with `math.floor`*: Rejected in favor of integer floor division `//` to completely prevent precision degradation on large paise values.
  - *Raising exceptions on invalid events*: Rejected because the evaluation specification and test contract dictate that invalid events should safely return the unmodified account structure.
- **Assumptions:**
  - Purchase amount and refund amount are in paise (1 INR = 100 paise = 10,000 paise per 100 rupees).
  - Transactions cannot be refunded for more than their original capture amount.
  - Running points balance cannot fall below zero.

## 5. Verification
- **Tests added or changed:**
  - Preserved all original tests in `tests/test_contract.py` and `tests/test_acceptance_matrix.py` without modification.
  - Created `tests/test_regression_and_edge_cases.py` with 6 new comprehensive tests covering:
    - Refund event replay idempotency.
    - Consecutive partial refunds accumulating to 100% without rounding drift.
    - Zero-awarded purchase refund safety.
    - Mathematical consistency between `points_balance` and ledger `points_delta` sum.
    - Defensive input handling for malformed/null/boolean values.
    - Account statement CSV generation.
- **Commands run and actual results:**
  - `python -m pytest -q`: `220 passed in 0.21s` (214 original + 6 new regression tests).
  - `python -m main`:
    ```text
    Points example: 27
    Repeat warnings: []
    ```
- **Edge cases verified:**
  - Paise boundaries (9,999 paise -> 0 pts, 10,000 paise -> 1 pt, 19,999 paise -> 1 pt).
  - Cap of zero points (`cap_points=0` -> 0 pts).
  - Duplicate event replaying (both purchase and refund events).
  - Over-refund protection (single excess refund and cumulative multi-step over-refund).
  - Non-integer input types (boolean, string, float, null, collections).
- **Remaining failures or known limitations:**
  - None. All 220 test cases pass cleanly with zero warnings or errors.
