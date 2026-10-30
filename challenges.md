# challenges.md

## 1. Challenge
Refunds that were too large or the wrong type. My first fix capped a big refund, but the test expected it to be ignored completely.

## 2. Evidence
- test_invalid_or_excess_refund_ignored failed with assert (100000 == 0).
- After that, the invalid refund test failed for True, None, "100", 1.5, a list and a dict (6 failed, 208 passed).

## 3. What I tried
1. Changed > to >= in the repeat alerts. That caused 48 failures, so I reverted it.
2. Capped the refund to the remaining amount. The test showed it should be ignored, so I changed it.
3. Added a bounds check. Six type cases still failed, so I added an integer type check.
4. Re-ran python -m pytest -q after every change.

## 4. Resolution
The root cause was missing input validation. Invalid refunds are now rejected before the balance or ledger is touched. I also fixed float division and the duplicate event check.

## 5. Proof
The refund tests and the replay/boundary tests. A case that could still break: a purchase with no transaction_id or a negative amount.

## 6. Next step
Add explicit checks for the purchase amount and a missing transaction_id, and test a refund replayed with a different event_id.