# approach.md - Required submission

## 1. Baseline
- **Commands run before editing:**
  - `python3 --version` → Python 3.15.0 on macOS Darwin arm64
  - `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt` (installed pytest 9.2.0)
  - `python -m pytest -q`
  - `python -m main`
- **Initial test result (actual summary):**
  - `67 failed, 147 passed in 0.21s` across 214 tests.
  - Failures grouped by root cause:
    - `test_integer_floor_points_calculation`: 11 failures — starter used `round(amount_paise / 10000)` which rounded up at `X9999`-paise boundaries instead of integer floor `// 10000`.
    - `test_bonus_and_cap_matrix`: 3 failures — `cap_points=0` was bypassed by `if cap_points:` (Python's truthiness treats `0` as `False`).
    - `test_purchase_event_replay_is_idempotent`: 20 failures — `processed_event_ids` was appended without a prior deduplication check, so replaying an event mutated state twice.
    - `test_capture_purchase_records_consistent_transaction`: 6 failures — floating-point rounding caused incorrect `awarded_points` in stored transactions.
    - `test_refund_amount_bounds_and_balance`: 10 failures — refund amounts were not validated before mutating `refunded_paise`.
    - `test_invalid_or_excess_refund_does_not_change_account`: 13 failures — negative refunds, booleans (`True`/`False`), strings, and over-refunds all mutated account state.
    - `test_contract.py` core failures: `test_points_use_floor`, `test_cap_zero_is_respected`, `test_purchase_event_once`, `test_invalid_or_excess_refund_ignored`.
- **Demo output before editing:**
  ```text
  Points example: 28
  Repeat warnings: []
  ```
  `28` appeared because `259900 / 10000.0 = 25.99`, which `round()` raised to `26`, then `26 * 110 // 100 = 28`. Correct integer floor: `259900 // 10000 = 25`, giving `25 * 110 // 100 = 27`.

## 2. Codebase understanding
- **Files inspected:**
  - `models.py`: `new_account(account_id)` — returns `{'account_id': ..., 'points_balance': 0, 'processed_event_ids': [], 'transactions': {}, 'ledger': []}`.
  - `service.py`: `calculate_points`, `apply_reward_event`, `flag_repeat_transactions`.
  - `fixtures.py`: Default sample account `ACCT-1001`, sample rules (`points_per_100_rupees=1`, `bonus_percent=10`, `cap_points=100`), and sample transactions.
  - `data/records.json` + `data/README.txt`: 40 accounts, 180 repeat-transaction records, 264 reward events, 180 captured purchases, 8 rule cases, 10 edge-case categories.
  - `tests/test_contract.py` and `tests/test_acceptance_matrix.py`: Traced every parametrized case and boundary assertion.
  - `.github/workflows/tests.yml`: Confirmed GitHub Actions runs `python -m pytest --junitxml` on push and PR.

- **Data flows traced:**
  - *Purchase flow:* `purchase_captured` event arrives → validate `event_id` (non-empty string, not already in `processed_event_ids`) → validate `transaction_id` → validate `amount_paise` (positive integer, not boolean) → `calculate_points(amount, rules...)` → if `transaction_id` is new, record transaction, credit `points_balance`, append ledger entry, append `event_id` to `processed_event_ids`.
  - *Refund flow:* `refund_processed` event arrives → validate `event_id` (not already processed) → validate `transaction_id` exists in `transactions` → validate `refund` is a positive integer (not boolean), cumulative `refunded_paise + refund ≤ original amount_paise` → compute `should_reverse = (awarded_points × new_refunded_paise) // original_amount` → clamp to `awarded_points` and current `points_balance` → deduct delta, update transaction state, append negative ledger entry, append `event_id`.
  - *Repeat-alert flow:* Group transactions by `(account_id, date, amount_paise)` → for any group where `len > threshold` (default 2, minimum 1), emit a review alert. Alerts are informational only and do not block any transaction.

- **Confirmation method:**
  - Manually traced 259900 paise through both the broken float path and the correct integer path on paper.
  - Ran failing tests individually and read assertion errors to confirm root causes before editing.

## 3. Investigation and implementation strategy

### Issue 1: Floating-point rounding causes wrong point counts (Req 1, 2)
- *Symptom:* `calculate_points(19999, 1)` returned `2`; should be `1`.
- *Root cause:* `round(amount_paise / 10000)` rounds half-up, violating Req 1's explicit floor rule.
- *Fix:* Replace with `(amount_paise // 10000) * points_per_100_rupees` and `(base * (100 + bonus_percent)) // 100`.
- *Evidence:* `test_points_use_floor` and 11 cases in `test_integer_floor_points_calculation`.

### Issue 2: `cap_points=0` bypassed by falsy check (Req 2)
- *Symptom:* `calculate_points(50000, 1, cap_points=0)` returned `5`; should be `0`.
- *Root cause:* `if cap_points:` in Python evaluates `0` as `False`, skipping the cap entirely.
- *Fix:* Changed to `if cap_points is not None:`.
- *Evidence:* `test_cap_zero_is_respected`.

### Issue 3: Event replay not blocked — no deduplication check at entry (Req 4)
- *Symptom:* Sending the same `purchase_captured` event twice doubled the balance.
- *Root cause:* `processed_event_ids.append(event_id)` was at the end, not guarded by an entry check.
- *Fix:* Added `if event_id in out['processed_event_ids']: return out` at the start of `apply_reward_event`.
- *Evidence:* 20 failures in `test_purchase_event_replay_is_idempotent`.

### Issue 4: Refunds mutated state before validation (Req 5, 6)
- *Symptom:* A refund of `150000` paise on a `100000` paise purchase mutated `refunded_paise` and reduced `points_balance`. Negative and boolean refund amounts also mutated state.
- *Root cause:* `txn['refunded_paise'] += refund` executed before the boundary check. No boolean or type guard on `refund`.
- *Fix:* Validate type and cumulative bound before touching any state. Compute `new_refunded_paise` locally, check `≤ original`, then write.
- *Evidence:* 23 failures in `test_invalid_or_excess_refund_does_not_change_account` and `test_refund_amount_bounds_and_balance`.

### Issue 5: Zero-paise purchases recorded in transactions (Req 2, 8)
- *Symptom:* A `purchase_captured` with `amount_paise=0` was not rejected; it created a transaction record and a ledger entry with `points_delta=0`. `calculate_points` already rejected `<= 0`, but the purchase branch only checked `< 0`.
- *Root cause:* Inconsistent boundary — purchase branch used `amount < 0`, `calculate_points` used `amount <= 0`.
- *Fix:* Changed purchase branch to `amount <= 0` to align boundaries. Req 2 states "invalid amounts must not generate points"; a zero-paise transaction is not a real purchase.
- *Evidence:* Identified during post-implementation audit; verified by updated `test_zero_amount_purchase_refund_branch`.

### Issue 6: `threshold ≤ 0` in `flag_repeat_transactions` falsely flags lone transactions (Req 7)
- *Symptom:* Passing `threshold=0` or `threshold=-1` caused every single transaction to be flagged as a repeat because `len(ids) > -1` is always `True`.
- *Root cause:* Guard only rejected `None`, non-int, and booleans. It passed through any negative or zero integer value as-is.
- *Fix:* Extended guard to `or threshold < 1`, defaulting any sub-1 threshold to `2`. Req 7 says "alerts are for human review only; never automatically accuse a customer" — flagging a single transaction as a repeat is exactly that.
- *Evidence:* Identified during audit; verified that `test_repeat_alert_threshold_input_is_handled` for `threshold=0` and `threshold=-1` still returns a valid list.

## 4. Implementation decisions
- **`deepcopy` for account immutability:** Req 8 implicitly and `test_input_account_not_mutated` explicitly require the caller's account to be untouched. `deepcopy` guarantees full isolation for all nested structures (`transactions`, `ledger`, `processed_event_ids`). Shallow copy would alias nested dicts and fail.
- **Kept `processed_event_ids` as a list:** Test assertions (`assert b['processed_event_ids'] == ['E1']`) and JSON-serialization compatibility require a list. A set would break both.
- **Stretch work — `generate_account_statement_csv`:** Implemented a single-pass `O(L)` CSV generator over the ledger with a running balance column. Chosen because it reuses the already-correct ledger structure with no additional state.
- **Rejected float alternatives:** `math.floor(amount_paise / 10000)` and `round()` both carry IEEE 754 representation risk on boundary values. Python integer `//` is exact.

## 5. Verification
- **Existing tests preserved:** All 214 baseline tests in `test_contract.py` and `test_acceptance_matrix.py` left unchanged — no deletions, skips, or assertion weakenings.
- **New regression tests added in `tests/test_regression.py`:**
  - `test_refund_event_replay_is_idempotent`
  - `test_cumulative_partial_refunds_and_over_refund_rejection`
  - `test_proportional_integer_truncation_across_multiple_refunds`
  - `test_zero_awarded_purchase_refund_safety`
  - `test_malformed_and_missing_identifiers_handling`
  - `test_cap_zero_and_negative_rules_safeguards`
  - `test_csv_account_statement_generation`
  - `test_purchase_captured_invalid_amount_safeguards`
  - `test_repeat_transactions_and_csv_statement_edge_cases`
  - `test_zero_amount_purchase_refund_branch`
- **Commands run and actual results:**
  - `python -m pytest -q`: `224 passed in 0.06s`
  - `python -m main`:
    ```text
    Points example: 27
    Repeat warnings: []
    Account points balance after refund: 17
    Statement CSV preview:
    event_id,type,points_delta,running_balance
    EVT-001,purchase_captured,27,27
    EVT-002,refund_processed,-10,17
    ```
- **Remaining failures or known limitations:**
  - Zero remaining test failures. All 224 tests pass cleanly.
  - In-memory only: a production deployment would need an event store and distributed locking (e.g., Kafka partition keys on `account_id`) to handle concurrent refunds safely.