# challenges.md - COMPULSORY submission

# 1. The tricky part

The refund validation gave me the most trouble, specifically test_invalid_or_excess_refund_does_not_change_account. That test feeds the code some strange inputs: True, False, None, "100", 1.5, [] and {}, plus negative and oversized amounts. The starter code simply ran txn['refunded_paise'] += refund. Anything non-numeric crashed with a TypeError. Bad numbers got through and quietly messed up the state.

# 2. Evidence

Here’s what the test run showed:

`FAILED tests/test_acceptance_matrix.py::test_invalid_or_excess_refund_does_not_change_account[None] - TypeError: unsupported operand type(s) for +=: 'int' and 'NoneType'`
`FAILED tests/test_acceptance_matrix.py::test_invalid_or_excess_refund_does_not_change_account[100] - TypeError: unsupported operand type(s) for +=: 'int' and 'str'`
`FAILED tests/test_acceptance_matrix.py::test_invalid_or_excess_refund_does_not_change_account[amount12] - TypeError: unsupported operand type(s) for +=: 'int' and 'list'`
`FAILED tests/test_acceptance_matrix.py::test_invalid_or_excess_refund_does_not_change_account[amount13] - TypeError: unsupported operand type(s) for +=: 'int' and 'dict'`
`FAILED tests/test_contract.py::test_invalid_or_excess_refund_ignored - assert (-1 == 0). A negative refund should leave refunded_paise at 0 and the balance untouched.`

# 3. What I tried

First, I opened service.py and read lines 23 to 28, where the refund block sits. It had no type check and no bounds check on refund at all.

Then I ran python -m pytest -q and kept the full list of failures. That let me split the parametrize cases into two groups: the ones that crashed with type errors and the ones that failed on assertions.

After that, I looked at how Python handles booleans. isinstance(True, int) returns True. So a plain isinstance(refund, int) check would wave True and False straight through. I added an explicit isinstance(refund, bool) exclusion to stop that.

# 4. The fix

The cause was simple. The refund block took any amount_paise value as it came. It never checked the type, the sign, or whether the amount was bigger than the original purchase.

I added a guard before anything gets changed:

```python
if not isinstance(refund, int) or isinstance(refund, bool) or refund <= 0 or refund > txn['amount_paise']:
    return out
```
Now every invalid input returns the account exactly as it was. No ledger entry, no balance change, and refunded_paise stays at 0. This deals with the real problem, which was the missing validation. Catching the TypeError afterwards would have hidden the symptom and left the damage in place.

# 5. Proof and regression prevention

These tests cover the fix:

test_invalid_or_excess_refund_does_not_change_account, all 15 parametrize cases
test_refund_amount_bounds_and_balance, for amounts over 100000
test_contract.py::test_invalid_or_excess_refund_ignored

There was one related case that could have caused trouble: a refund event for a transaction_id that isn’t in out['transactions']. The existing elif kind=='refund_processed' and txn_id in out['transactions'] condition already covers it. The event is simply ignored.

# 6. Open issues and next steps

Nothing is left unresolved, and all 214 tests pass. If I had more time, I’d add property-based tests with something like Hypothesis, to throw a much wider range of refund amounts and event IDs at the code. I’d also add integration tests that simulate concurrent event replay.