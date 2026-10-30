# challenges.md - COMPULSORY submission

## 1. Challenge or confusing behaviour
The most intricate challenge was ensuring exact mathematical correctness during **multi-step proportional refund reversals** without introducing integer truncation drift, combined with Python's type hierarchy subtlety where `bool` is a subclass of `int`. 

Specifically:
1. When refunds occur in multiple partial installments (e.g., 30%, then 30%, then 40%), calculating the reversal delta independently on each installment could lead to rounding discrepancies compared to calculating based on cumulative refunded amounts.
2. The test suite tested inputs like `True` and `False` as refund amounts and rule values. In Python, `isinstance(True, int)` returns `True`, meaning standard `isinstance(val, int)` checks alone mistakenly allowed boolean values through as `1` or `0`.
3. In `calculate_points()`, the starter wrote `if cap_points:`, which unintentionally skipped the cap when `cap_points == 0` because `0` evaluates to falsy in Python.

## 2. Evidence
1. **Boolean Type Leak**:
   In `tests/test_acceptance_matrix.py`:
   ```python
   @pytest.mark.parametrize("amount", [..., True, None, "100", 1.5, [], {}, False])
   def test_invalid_or_excess_refund_does_not_change_account(amount):
   ```
   When running with a naive check `if not isinstance(refund, int): return out`, Python treated `True` as `1` and `False` as `0`. `True` caused a 1-paise refund to be processed instead of being rejected as an invalid type.

2. **Cap Zero Bug**:
   In `tests/test_contract.py`:
   ```python
   def test_cap_zero_is_respected():
       assert calculate_points(50000, 1, cap_points=0) == 0
   ```
   Assertion error showed `assert 5 == 0`. The starter code evaluated `if cap_points:` which was `False` when `cap_points = 0`, thus never applying the cap.

3. **Cumulative Refund Reversals**:
   If a customer makes a 100,000 paise purchase earning 10 points and receives three partial refunds:
   - Refund 1: 33,333 paise
   - Refund 2: 33,333 paise
   - Refund 3: 33,334 paise
   If reversals were calculated per-event as `(10 * 33333) // 100000 = 3` and `(10 * 33334) // 100000 = 3`, the total points reversed would only be `3 + 3 + 3 = 9`, failing to reverse the final 10th point upon 100% refund.

## 3. What I tried
- **Experiment 1 (Type checking)**: Tested `isinstance(True, int)` in the Python REPL and observed it returns `True`. Tested `type(True) is int`, which returns `False`. However, `isinstance(x, bool)` explicitly flags booleans.
- **Experiment 2 (Per-refund delta vs. cumulative reversal tracking)**: Tested calculating reversal deltas strictly on the delta refund `(awarded * refund) // total` versus calculating cumulative target points reversed `(awarded * cumulative_refunded) // total` and taking the difference from previously reversed points.
- **Experiment 3 (Idempotency ordering)**: Investigated whether `processed_event_ids` should be updated for rejected events (e.g. invalid refunds or declined purchases). Tested how subsequent retries behaved if an event was initially malformed versus validly accepted.

## 4. Resolution
1. **Explicit Boolean Rejection**:
   Added `isinstance(val, bool)` checks before accepting integer amounts across both `calculate_points()` and `apply_reward_event()`:
   ```python
   if isinstance(refund, bool) or not isinstance(refund, int) or refund <= 0:
       return out
   ```
2. **Cumulative Reversal Calculation**:
   Structured the refund reversal using cumulative state tracking on the transaction record:
   ```python
   txn["refunded_paise"] += refund
   should_reverse = (txn["awarded_points"] * txn["refunded_paise"]) // txn["amount_paise"]
   should_reverse = min(should_reverse, txn["awarded_points"])
   should_reverse = max(should_reverse, txn["reversed_points"])
   delta = should_reverse - txn["reversed_points"]
   delta = min(delta, out["points_balance"])
   delta = max(0, delta)
   out["points_balance"] -= delta
   txn["reversed_points"] += delta
   ```
   By tracking `txn["refunded_paise"]` cumulatively, subsequent partial refunds naturally recover any previous integer floor truncation, guaranteeing that full refunds always reverse 100% of awarded points.
3. **Explicit None Check for Cap**:
   Replaced `if cap_points:` with:
   ```python
   if cap_points is not None:
       if isinstance(cap_points, bool) or not isinstance(cap_points, int) or cap_points < 0:
           return 0
       if cap_points == 0:
           return 0
       points = min(points, cap_points)
   ```

## 5. Proof and regression prevention
- **Proof**:
  - `test_cap_zero_is_respected` in `tests/test_contract.py` passed immediately.
  - `test_invalid_or_excess_refund_does_not_change_account` passed for all 15 parametrized boundary cases including `True`, `False`, and `None`.
  - Added `test_sequential_partial_refunds_up_to_full_amount` in `tests/test_regression_and_edge_cases.py`, verifying that three successive partial refunds (30k, 30k, 40k) on a 100k purchase reverse exactly 3, 3, and 4 points, reaching exactly 0 balance and 10 reversed points.
- **Related cases that could break**:
  - An account that has redeemed or transferred points prior to a refund event could potentially experience a negative balance if `delta` were not clamped by `out['points_balance']`. The implemented safeguard `delta = min(delta, out['points_balance'])` prevents negative balances under all conditions.

## 6. Unresolved challenge or next step
- Currently, the ledger records net point changes per accepted event. If points redemption or expiration events are introduced in future extensions, the transaction data model should link redemptions to specific purchase transaction IDs or implement FIFO point buckets to handle partial-redemption clawbacks transparently.
