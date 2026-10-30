# Testing — RewardBook

## Test setup

I used the following environment to run the tests:

- Python version: Python 3.14.4
- Test framework: pytest
- Command: `python -m pytest -q`

The first time I ran the tests, the result was:

```text
147 passed, 67 failed
```

After making the changes, I ran the full test suite again and got:

```text
214 passed
```

The first test run showed problems in reward calculation, bonus and cap handling, duplicate events, and refund validation.

## Edge cases I checked

| No. | Input / case | Expected result | Test result |
|---|---|---|---|
| 1 | Purchase amount is 19,999 paise | 1 point at 1 point per ₹100 | Passed |
| 2 | Points cap is 0 | Final points should be 0 | Passed |
| 3 | Same purchase event is processed again | Points and ledger should not be updated twice | Passed |
| 4 | Refund is more than the original purchase amount | Refund should be rejected without changing the balance | Passed |
| 5 | ₹500 refund on a ₹1,000 purchase | 50% of the awarded points should be reversed | Passed |
| 6 | Purchase is declined | No reward points should be given | Passed |
| 7 | Similar transactions belong to different accounts | They should not be grouped together | Passed |

These cases are covered by the existing tests in `tests/test_contract.py` and `tests/test_acceptance_matrix.py`.

## What the existing tests cover

The test files check:

- Reward points are calculated using floor division.
- Bonus percentage and points cap are applied correctly.
- A zero points cap is handled correctly.
- The same event ID is not processed more than once.
- Purchase transaction details match the points awarded.
- Invalid and excessive refunds are rejected.
- Partial refunds reverse points proportionally.
- Unknown and declined events do not award points.
- Repeat transactions are grouped using account, date and amount.
- Repeat-alert threshold conditions work.
- The original account object is not changed by event processing.

I did not change the existing test files.

## Things not fully tested yet

There are still some cases that need more testing:

- Missing or empty event IDs and transaction IDs.
- Invalid purchase amount types.
- Invalid reward-rule types.
- Database storage and handling multiple events at the same time.

The repeat-alert function uses `count > threshold`. These alerts only show possible repeated patterns for someone to review. They do not prove fraud or block a transaction.

The latest full test run completed with 214 passing tests and no reported failures.