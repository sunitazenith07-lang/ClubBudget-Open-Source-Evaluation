# challenges.md - COMPULSORY submission

This file is mandatory and worth 5 marks. Describe your actual experience honestly. Do not invent difficulties to fill the page.

## 1. Challenge or confusing behaviour
The most subtle and critical challenges encountered during debugging were:
1. **The `dict.setdefault()` Null-Trap on Corrupted Accounts:** When an account dictionary already contains keys with explicit `None` values (e.g. `{'points_balance': None, 'processed_event_ids': None, 'transactions': None, 'ledger': None}`), calling `out.setdefault("processed_event_ids", [])` does NOT populate the default because the key already exists! Later in execution, `if event_id in out["processed_event_ids"]:` crashes with `TypeError: argument of type 'NoneType' is not iterable`.
2. **`bonus_percent=None` Premature Zeroing:** When rules omit `bonus_percent` or pass `None` explicitly, a strict `isinstance(bonus_percent, int)` check causes `calculate_points()` to award `0` points even on valid purchases, instead of treating `bonus_percent=None` as "no bonus" (0%).
3. **`threshold=None` Runtime Type Error:** In `flag_repeat_transactions()`, if `threshold=None` is supplied, `len(ids) > threshold` crashes with `TypeError: '>' not supported between instances of 'int' and 'NoneType'`.
4. **Python Boolean Subclassing:** `bool` is a subclass of `int` in Python, so `isinstance(True, int)` is `True`. Without explicit `not isinstance(x, bool)` checks, boolean values passed as amounts or rates are treated as integer 1 or 0.

## 2. Evidence
- Corrupted account crash:
  ```text
  TypeError: argument of type 'NoneType' is not iterable
  File "service.py", in apply_reward_event
    if event_id in out["processed_event_ids"]:
  ```
- `threshold=None` crash:
  ```text
  TypeError: '>' not supported between instances of 'int' and 'NoneType'
  File "service.py", in flag_repeat_transactions
    if len(ids) > threshold
  ```
- `test_invalid_or_excess_refund_does_not_change_account[True]`:
  ```text
  FAILED tests/test_acceptance_matrix.py::test_invalid_or_excess_refund_does_not_change_account[True]
  assert result["transactions"]["T"]["refunded_paise"] == 0
  ```

## 3. What I tried
1. **Account field sanitization:** Initially relied on `out.setdefault()`. When reproducing null-field edge cases, discovered `setdefault()` preserves existing `None` values. Replaced it with explicit type validation:
   ```python
   if not isinstance(out.get("processed_event_ids"), list):
       out["processed_event_ids"] = []
   ```
2. **Rule defaults:** Added explicit normalization for `bonus_percent is None` (defaulting to 0) and `points_per_100_rupees is None` (defaulting to 1).
3. **Threshold normalization:** Added fallback `if threshold is None or not isinstance(threshold, int) or isinstance(threshold, bool): threshold = 2`.
4. **Boolean exclusion:** Applied `not isinstance(x, bool)` across all integer parameters.

## 4. Resolution
- Replaced naive `setdefault()` calls with deep defensive type checking for all container fields (`processed_event_ids`, `transactions`, `ledger`, `points_balance`).
- Handled `None` gracefully across rule inputs and threshold values.
- Enforced strict bounds check `refunded_paise + refund <= amount_paise` for refund events.
- Enforced cross-account event rejection when `event['account_id'] != account['account_id']`.

## 5. Proof and regression prevention
- **Proof:** All 229 tests pass with 0 failures in 0.17s.
- **Regression Tests Added in `tests/test_regression.py`:**
  - `test_bonus_percent_none_defaults_to_zero`
  - `test_corrupted_or_null_account_fields_handled_safely`
  - `test_cross_account_event_rejected`
  - `test_rules_with_none_values_use_proper_defaults`
  - `test_threshold_none_or_invalid_defaults_to_two`
  - `test_non_int_types_award_zero`
  - `test_refund_event_idempotency`

## 6. Unresolved challenge or next step
- For high-concurrency production deployments, account mutations should be isolated using database row-level locking (`SELECT ... FOR UPDATE`) or an append-only event sourcing stream to eliminate race conditions between concurrent requests.