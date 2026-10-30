# approach.md - Required submission

## 1. Baseline
- **Commands run before editing:**
  - `python3 --version` (Environment: Python 3.15.0 on macOS Darwin arm64)
  - `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt` (installed pytest 9.2.0)
  - `python -m pytest -q`
  - `python -m main`
- **Initial test result (actual summary):**
  - Baseline execution failed: `67 failed, 147 passed in 0.21s` across 214 tests.
  - Failures spanned:
    - `test_integer_floor_points_calculation` (11 failures due to `round()` rounding up at `X9999` paise boundaries instead of integer floor `// 10000`).
    - `test_bonus_and_cap_matrix` (3 failures, including `cap_points=0` being bypassed by falsy check `if cap_points:`).
    - `test_purchase_event_replay_is_idempotent` (20 failures due to `processed_event_ids` appending duplicates and reapplying events).
    - `test_capture_purchase_records_consistent_transaction` (6 failures due to rounding).
    - `test_refund_amount_bounds_and_balance` (10 failures due to unvalidated refund amounts).
    - `test_invalid_or_excess_refund_does_not_change_account` (13 failures: negative refunds, zero refunds, non-integer types like `True`, strings, floats, and collections mutating state).
    - `test_contract.py` (4 core contract failures: `test_points_use_floor`, `test_cap_zero_is_respected`, `test_purchase_event_once`, `test_invalid_or_excess_refund_ignored`).
- **Demo/output observed:**
  ```text
  Points example: 28
  Repeat warnings: []
  ```
  Points example returned `28` because 259900 paise was divided by 10000 giving 25.99, rounded to 26, then multiplied by 110 // 100 = 28 points. Under integer floor arithmetic, `259900 // 10000` is 25, giving `25 * 110 // 100 = 27` points.

## 2. Codebase understanding
- **Important files/functions inspected:**
  - `models.py`: Inspected `new_account(account_id)`, noting default structure: `{'account_id': account_id, 'points_balance': 0, 'processed_event_ids': [], 'transactions': {}, 'ledger': []}`.
  - `service.py`: Inspected `calculate_points`, `apply_reward_event`, and `flag_repeat_transactions`.
  - `fixtures.py`: Inspected default sample account `ACCT-1001`, sample rules, and sample transactions.
  - `data/records.json` and `data/README.txt`: Inspected expanded synthetic dataset comprising 40 accounts, 180 repeat-transaction records, 264 reward events, 180 captured purchases, 8 rule cases, and 10 edge-case categories.
  - `tests/test_contract.py` & `tests/test_acceptance_matrix.py`: Analyzed every parameterized test case, contract assertion, and boundary condition.
- **Rewards calculation, refund, ledger or alert flow traced:**
  - *Purchase Flow:* An incoming `purchase_captured` event contains `event_id`, `type`, `transaction_id`, and `amount_paise`. If `event_id` is new, calculate points via integer floor: `base_points = (amount_paise // 10000) * points_per_100_rupees`, `bonus_points = (base_points * (100 + bonus_percent)) // 100`, bounded by optional `cap_points`. Credit account `points_balance`, record transaction state (`amount_paise`, `awarded_points`, `reversed_points`, `refunded_paise`), append delta to `ledger`, and mark `event_id` in `processed_event_ids`.
  - *Refund Flow:* An incoming `refund_processed` event targets an existing `transaction_id`. Must validate that `refund_paise` is positive integer and cumulative `refunded_paise + refund <= original amount_paise`. Calculate proportional integer reversal: `should_reverse = (awarded_points * cumulative_refund) // original_amount`, clamp by awarded points and current balance, compute `delta = should_reverse - reversed_points`, deduct `delta` from balance, record negative ledger delta, and mark `event_id` in `processed_event_ids`.
  - *Repeat Warning Flow:* Group transactions by composite key `(account_id, date, amount_paise)`. If group size exceeds `threshold` (default 2), generate a review alert containing account, date, amount, and transaction IDs sorted deterministically.
- **How you confirmed your understanding:**
  - Traced calculation manually on paper with 259900 paise and compared with starter output.
  - Traced failure stack traces from pytest to verify exact assertion expectations for idempotency and refund bounds.

## 3. Investigation and implementation strategy
- **Issue 1: Incorrect Points Calculation & Rule Boundary Failures**
  - *Symptom:* `calculate_points(19999, 1)` returned `2` instead of `1`. `calculate_points(50000, 1, cap_points=0)` returned `5` instead of `0`. Invalid/negative rules and types raised unexpected results.
  - *Hypothesis:* Starter code utilized floating-point `round(amount_paise / 10000)` instead of integer floor `// 10000`. In Python, `if cap_points:` evaluates `0` to `False`, completely bypassing a cap of 0. Furthermore, negative amounts and boolean values (`True`/`False`) were treated as integers without explicit type guards.
  - *Evidence:* Pytest failures in `test_points_use_floor`, `test_cap_zero_is_respected`, and 14 parameterized cases in `test_acceptance_matrix.py`.
  - *Fix Chosen:* Enforce integer floor arithmetic `(amount_paise // 10000) * points_per_100_rupees`, validate that amounts and rules are non-boolean positive/non-negative integers, and check `if cap_points is not None:` to honor `cap_points = 0`.
- **Issue 2: Idempotency Defect & Replay Vulnerability**
  - *Symptom:* Replaying an identical `purchase_captured` or `refund_processed` event mutated `processed_event_ids` to `['E1', 'E1']` and risked double-crediting/double-reversing.
  - *Hypothesis:* The starter function appended `event_id` to `processed_event_ids` unconditionally at the end of `apply_reward_event`, without checking if `event_id in out['processed_event_ids']` beforehand.
  - *Evidence:* 20 pytest failures in `test_purchase_event_replay_is_idempotent` where `twice["processed_event_ids"] == ['PURCHASE-000', 'PURCHASE-000']`.
  - *Fix Chosen:* Insert early return `if event_id in out['processed_event_ids']: return out` at the top of event processing. Validate `event_id` is a non-empty string.
- **Issue 3: Unvalidated Refunds and Ledger Discrepancies**
  - *Symptom:* Negative refunds (`amount_paise: -1`), non-numeric types (`None`, `True`, `"100"`), and over-refunds (`150000` on a `100000` purchase) mutated account balance and added corrupted entries to ledger.
  - *Hypothesis:* Starter updated `txn['refunded_paise'] += refund` before validating against `txn['amount_paise']` and lacked strict type checking. It also lacked clamping to prevent `points_balance` from dropping below 0.
  - *Evidence:* 23 pytest failures in `test_invalid_or_excess_refund_does_not_change_account` and `test_refund_amount_bounds_and_balance`.
  - *Fix Chosen:* Validate `isinstance(refund, int) and not isinstance(refund, bool) and refund > 0`. Ensure `txn['refunded_paise'] + refund <= txn['amount_paise']`. Calculate cumulative proportional reversal, clamp `delta` so `points_balance` never goes negative, update transaction state, and only write ledger entries for accepted refunds.

## 4. Implementation decisions
- **Main changes and why:**
  - Strict type and boundary guards in `calculate_points` and `apply_reward_event` (`not isinstance(x, bool) and isinstance(x, int)`): prevents booleans (`True == 1`) from being accepted as monetary amounts or multipliers.
  - Implemented `generate_account_statement_csv(account)` as the optional stretch work deliverable: allows finance operations to export an auditable ledger with running point balances in standard CSV format.
  - Robust repeat-alert handling in `flag_repeat_transactions`: safely validates non-dict transactions, missing identifiers, and non-integer thresholds, preserving deterministic sorting by stringified group key.
- **Alternatives considered and why rejected:**
  - *Alternative: Floating-point math with `math.floor`:* Rejected because IEEE 754 float precision issues can cause subtle rounding discrepancies (e.g., `29999 / 10000.0` or float division with bonuses). Native integer arithmetic (`//`) is exact and strictly required by specification.
  - *Alternative: Raising exceptions on invalid events/refunds:* Rejected because financial ingestion pipelines require fault-tolerant stream handling where malformed or out-of-order events are safely ignored without crashing the processor or corrupting state.
- **Assumptions:**
  - An event without a valid string `event_id` or `transaction_id` is considered malformed and safely ignored.
  - Transactions for repeat alerts must retain raw key attributes `(account_id, date, amount_paise)` to ensure exact grouping.

## 5. Verification
- **Tests added or changed:**
  - Kept all 214 existing baseline tests in `tests/test_contract.py` and `tests/test_acceptance_matrix.py` intact without weakening or modifying them.
  - Added new dedicated test suite `tests/test_regression.py` containing 10 comprehensive regression tests:
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
  - `python -m pytest -q`: `224 passed in 0.06s` (100% pass rate).
  - `python -m pytest -q --junitxml=/tmp/pytest-report.xml`: verified XML report generation for GitHub Actions CI compatibility.
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
- **Edge cases verified:**
  - Paise boundary values (e.g. 9999, 10000, 19999, 20000).
  - Zero cap (`cap_points=0`) and negative rule values.
  - Multi-step cumulative partial refunds summing exactly to purchase amount.
  - Over-refund rejections (cumulative refund > purchase amount).
  - Replay of both purchase and refund events.
  - Negative balance prevention.
  - Malformed and non-integer inputs (`None`, `True`, `False`, `"100"`, `1.5`, `[]`, `{}`).
- **Remaining failures or known limitations:**
  - Zero remaining test failures. All 224 tests pass cleanly.