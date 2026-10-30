# challenges.md - COMPULSORY submission

## 1. Challenge or confusing behaviour
The most intricate challenge involved two coupled domain complexities:
1. **Cumulative Integer Truncation in Sequential Partial Refunds:**
   Calculating refund reversals independently per event using `(awarded_points * refund_amount) // purchase_amount` causes truncation drift over sequential partial refunds. For example, on a purchase of 100,000 paise (awarding 10 points), three partial refunds of 33,333, 33,333, and 33,334 paise would individually each calculate `(10 * 33333) // 100000 = 3` points, reversing only 9 points total despite 100% of the money being refunded.
2. **Subtle Python Type Hierarchy Traps (`bool` subclassing `int`):**
   In Python, `bool` is a direct subclass of `int` (`issubclass(bool, int) is True`, and `isinstance(True, int) is True`). Consequently, passing `True` or `False` into functions with basic `isinstance(val, int)` guards results in `True` being treated as `1` (1 paise or 1 point rule). In `test_invalid_or_excess_refund_does_not_change_account`, test parameters included `[True, False, 1.5, "100", [], {}]`. Without explicit boolean rejection, `True` was accepted as an amount of 1 paise and processed as a valid refund!

## 2. Evidence
- **Test failure output for type confusion:**
  ```text
  FAILED tests/test_acceptance_matrix.py::test_invalid_or_excess_refund_does_not_change_account[True]
  FAILED tests/test_acceptance_matrix.py::test_invalid_or_excess_refund_does_not_change_account[False]
  E   assert 1 == 0
  E    +  where 1 = result["transactions"]["T"]["refunded_paise"]
  ```
  `True` was treated as `1` paise, modifying the transaction's `refunded_paise` from `0` to `1` when it should have been rejected as an invalid refund payload.
- **Contract failure for cap zero:**
  ```text
  FAILED tests/test_contract.py::test_cap_zero_is_respected
  E   assert 5 == 0
  E    +  where 5 = calculate_points(50000, 1, cap_points=0)
  ```
  `if cap_points:` in Python evaluates `0` to `False`, completely skipping the cap check and returning 5 points instead of 0.

## 3. What I tried
1. **Initial Tracing:**
   I traced `apply_reward_event` line by line with a debugger and isolated where `True` was accepted. In Python's REPL, evaluating `isinstance(True, int)` confirmed it returns `True`.
2. **Testing Naive Per-Event Refund Calculations vs Cumulative Calculation:**
   I simulated splitting an order into three partial refunds. A per-event calculation resulted in un-reversed residual points. The starter implementation had attempted a cumulative formula:
   ```python
   should_reverse = txn['awarded_points'] * txn['refunded_paise'] // max(1, txn['amount_paise'])
   ```
   However, the starter executed `txn['refunded_paise'] += refund` *before* validating whether `txn['refunded_paise'] + refund <= txn['amount_paise']`, thereby corrupting the transaction ledger on over-refund attempts before failing or partially applying.
3. **Type Guard Refinement:**
   I tested adding `isinstance(val, int) and not isinstance(val, bool)` across all monetary inputs (`amount_paise`, `points_per_100_rupees`, `bonus_percent`, `cap_points`).

## 4. Resolution
- **Root Cause:**
  - Python's standard `int` type check accepts booleans.
  - Python's truthiness evaluates `0` as falsy, leading `if cap_points:` to bypass zero caps.
  - State mutation (`txn['refunded_paise'] += refund`) occurred before boundary and cumulative cap checks.
- **Exact Fix Applied:**
  1. Enforced strict validation:
     ```python
     if not isinstance(refund, int) or isinstance(refund, bool) or refund <= 0:
         return out
     if txn['refunded_paise'] + refund > txn['amount_paise']:
         return out
     ```
  2. Applied cumulative proportional integer calculation based on `new_refunded_paise`:
     ```python
     new_refunded_paise = txn['refunded_paise'] + refund
     should_reverse = (awarded * new_refunded_paise) // orig_amount
     should_reverse = min(should_reverse, awarded)
     delta = max(0, should_reverse - txn['reversed_points'])
     delta = min(delta, out['points_balance'])
     ```
  3. Checked `cap_points is not None` in `calculate_points`:
     ```python
     if cap_points is not None:
         if not isinstance(cap_points, int) or isinstance(cap_points, bool) or cap_points < 0:
             return 0
         bonus_points = min(bonus_points, cap_points)
     ```

## 5. Proof and regression prevention
- **Tests demonstrating the fix:**
  - `test_cap_zero_is_respected` and `test_bonus_and_cap_matrix[50000-2-50-0-0]` pass cleanly.
  - `test_invalid_or_excess_refund_does_not_change_account` across all 15 boundary types (including `True`, `False`, `None`, `"100"`, `1.5`, `[]`, `{}`) passes cleanly.
  - New regression test `test_cumulative_partial_refunds_and_over_refund_rejection` in `tests/test_regression.py` explicitly tests sequential 30% and 70% refunds followed by an over-refund rejection.
  - New regression test `test_proportional_integer_truncation_across_multiple_refunds` verifies integer truncation across 3 sequential refunds of 10,000 paise on a 30,000 paise purchase.
- **Related cases that could break if altered:**
  - If someone replaces `if cap_points is not None:` with `if cap_points:`, `cap_points=0` will immediately break.
  - If someone removes `not isinstance(x, bool)`, boolean amounts like `True` will re-enter the ledger.

## 6. Unresolved challenge or next step
- In this offline service, accounts and transactions are held in memory as dictionary structures. If transactions were to arrive concurrently across distributed worker threads, race conditions could occur during event replay or refund validation. In a production deployment, atomic database transactions with row-level locks or an event-sourcing log (such as Kafka with partition keys on `account_id`) would be required to maintain ledger consistency.