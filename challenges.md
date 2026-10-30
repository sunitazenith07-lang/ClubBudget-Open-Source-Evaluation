# challenges.md - COMPULSORY submission

## 1. Challenges encountered

Three concrete technical obstacles required careful investigation and testing to resolve.

---

### Challenge A: Cumulative Integer Truncation in Sequential Partial Refunds (Req 5)

**The obstacle:** Requirement 5 demands proportional point reversal using integer arithmetic, but applying the reversal calculation independently per refund event causes truncation drift. For example: purchase of `30000` paise awards `3` points. Three sequential refunds of `10000` paise each must collectively reverse all `3` points. If each refund independently calculates `(3 × 10000) // 30000 = 1`, you reverse `1 + 1 + 1 = 3` correctly — but only by accident. A purchase of `100000` paise (10 points) with three refunds of `33333`, `33333`, `33334` paise computes `(10 × 33333) // 100000 = 3` per event — reversing only `9` despite a full 100% refund. This is the truncation drift problem.

**Investigation:** I ran the sequential refund manually through the broken starter implementation and confirmed via test failures in `test_refund_amount_bounds_and_balance` that balances after refunds were consistently off. I then traced the formula: the fix is to track `reversed_points` cumulatively on the transaction and compute `should_reverse = (awarded_points × cumulative_refunded_paise) // original_amount` at each step, then `delta = should_reverse - reversed_points_so_far`. This always produces the correct total over any sequence of partial refunds.

**Resolution:**
```python
new_refunded_paise = txn['refunded_paise'] + refund
should_reverse = (awarded * new_refunded_paise) // orig_amount
should_reverse = min(should_reverse, awarded)
delta = max(0, should_reverse - txn['reversed_points'])
delta = min(delta, out['points_balance'])
```

**Proof:** `test_cumulative_partial_refunds_and_over_refund_rejection` applies 30% then 70% refunds; `test_proportional_integer_truncation_across_multiple_refunds` applies three 1/3 refunds on 30000 paise. Both pass cleanly.

---

### Challenge B: Python's `bool` Subclasses `int` — Silent Type Coercion (Req 2, 5)

**The obstacle:** In Python, `bool` is a subclass of `int`. `isinstance(True, int)` returns `True`, and `True == 1`, `False == 0`. This meant passing `True` as `amount_paise` passed the basic `isinstance(amount_paise, int)` guard and was treated as a valid 1-paise amount, creating a transaction and refund entry that should not exist.

**Evidence from test output:**
```text
FAILED tests/test_acceptance_matrix.py::test_invalid_or_excess_refund_does_not_change_account[True]
E   assert 1 == 0
E    +  where 1 = result["transactions"]["T"]["refunded_paise"]
```
`True` was accepted as `1` paise and modified `refunded_paise` from `0` to `1`, which should have been rejected.

**Investigation:** Confirmed in Python REPL:
```python
>>> isinstance(True, int)
True
>>> True + 0
1
```

**Resolution:** Added explicit boolean rejection guard to every monetary and rule input:
```python
if not isinstance(amount_paise, int) or isinstance(amount_paise, bool) or amount_paise <= 0:
    return 0
```
Applied consistently to `amount_paise`, `points_per_100_rupees`, `bonus_percent`, `cap_points`, and refund `amount_paise`.

**Proof:** `test_invalid_or_excess_refund_does_not_change_account[True]`, `test_invalid_or_excess_refund_does_not_change_account[False]`, and `test_cap_zero_and_negative_rules_safeguards` all pass.

---

### Challenge C: `threshold ≤ 0` in `flag_repeat_transactions` Flags Every Transaction as a Repeat (Req 7)

**The obstacle:** Requirement 7 says alerts must be for human review only and must never automatically accuse a customer. When `threshold=0` or `threshold=-1` is passed, the condition `len(ids) > threshold` evaluates to `True` for every single transaction — including lone transactions — flagging them as repeats. A threshold of `-1` means a group of 1 transaction is flagged. This directly contradicts Req 7's intent.

**Investigation:** Traced the guard on line 148 of `service.py`:
```python
if threshold is None or not isinstance(threshold, int) or isinstance(threshold, bool):
    threshold = 2
```
This guard handled `None`, non-ints, and booleans, but passed through any valid integer including `0` and `-1`. Running `flag_repeat_transactions([{'transaction_id':'1','account_id':'A','date':'D','amount_paise':1000}], threshold=-1)` returned that single transaction as a flagged repeat — wrong.

**Resolution:** Extended the guard to reject any threshold below `1`:
```python
if threshold is None or not isinstance(threshold, int) or isinstance(threshold, bool) or threshold < 1:
    threshold = 2
```

**Proof:** `test_repeat_alert_threshold_input_is_handled[0]`, `[-1]`, `[-5]` all pass (result is `isinstance(result, list)`). Manual verification confirms a single transaction is no longer incorrectly flagged.

---

## 2. Hardest deliberate edge case tested

Beyond the obstacles above, the trickiest deliberate test was **cumulative over-refund rejection after two valid partial refunds.** After applying a 30% refund (R-1, accepted) and a 70% refund (R-2, accepted, fully exhausting `amount_paise`), a third refund of even `1` paise (R-3) must be completely rejected — no ledger entry, no balance change, and `R-3` must not appear in `processed_event_ids`. This tests that the cumulative bound check `txn['refunded_paise'] + refund > txn['amount_paise']` is evaluated with the *already-updated* `refunded_paise` of `100000`, and that a rejected refund event is not silently marked as processed.

Test: `test_cumulative_partial_refunds_and_over_refund_rejection` in `tests/test_regression.py`.

## 3. Unresolved limitation

The implementation is fully in-memory. In a concurrent multi-worker deployment, two refund events arriving simultaneously for the same `transaction_id` could both pass the `refunded_paise + refund <= amount_paise` check before either writes back. Production would require atomic database transactions or partition-keyed event queue processing (e.g., Kafka with `account_id` as partition key) to maintain ledger consistency.