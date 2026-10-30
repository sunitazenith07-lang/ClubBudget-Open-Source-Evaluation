# TESTING.md

## Test command and environment
- Python version: 3.14.6
- Command run: python -m pytest -q
- Test summary: 214 passed in 0.87s

## Edge cases

1. **Amount just under a 100-rupee boundary**
   Input: 19,999 paise at 1 point per Rs 100.
   Expected: 1 point (rounded down). Result: 1 point.
   Test: covered by the existing tests in tests/

2. **Cap of zero**
   Input: cap_points = 0.
   Expected: 0 points. Result: 0 points.
   Test: covered by the existing tests in tests/

3. **Same event sent twice**
   Input: the same event_id replayed.
   Expected: balance and ledger do not change the second time. Result: no change.
   Test: covered by the existing tests in tests/

4. **Refund bigger than the purchase**
   Input: refund larger than the amount still refundable.
   Expected: ignored. Result: account unchanged.
   Test: test_invalid_or_excess_refund_ignored

5. **Refund with a wrong type**
   Input: True, None, "100", 1.5, a list or a dict.
   Expected: ignored, no crash. Result: account unchanged.
   Test: test_invalid_or_excess_refund_does_not_change_account

6. **Different accounts, same date and amount**
   Expected: not flagged as a repeat. Result: no alert.
   Test: test_different_accounts_not_grouped

## Regression tests added
No new tests added. The fixes are protected by the existing suite in tests/ (214 tests).

## Remaining limitations
None known. All 214 tests pass.