# TESTING.md

## Test command and environment

- **Python version:** Python 3.10+ was the project requirement. The exact installed Python version was not recorded.
- **Commands run:**

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m main
```

- **Actual test summary:**

Initial test run:

```text
67 failed, 147 passed in 1.30s
```

Final test run after implementation and regression tests:

```text
221 passed in 0.46s
```

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | Negative purchase amount | Invalid negative amounts should not earn reward points. | Passed | `test_negative_amount` |
| 2 | Zero reward point cap | The final reward should be zero when the configured cap is zero. | Passed | `test_zero_cap` |
| 3 | Duplicate event ID | The same event should not be processed more than once. | Passed | `test_duplicate_event` |
| 4 | Refund greater than original purchase | The refund should be rejected without exceeding the original purchase amount. | Passed | `test_refund_greater_than_purchase` |
| 5 | Refund for unknown transaction | An unknown transaction should not change the account balance or ledger. | Passed | `test_unknown_transaction_refund` |
| 6 | Partial refund | Points should be reversed proportionally to the cumulative refunded amount. | Passed | `test_partial_refund` |
| 7 | Empty repeat transaction list | The function should return an empty alert list. | Passed | `test_empty_repeat_transactions` |

All seven cases are covered by the added regression test file, `tests/test_regressions.py`. The final full test suite reported 221 passing tests.

## Regression tests added

I added `tests/test_regressions.py` with seven tests to prevent the identified issues from returning.

The tests cover:

- Negative purchase amounts and invalid reward inputs.
- Correct handling of a zero-point cap.
- Duplicate event processing.
- Refunds exceeding the original purchase amount.
- Refunds for transactions that do not exist.
- Proportional point reversal for partial refunds.
- Empty input for repeat transaction alerts.

The implementation changes protected by these tests include integer-based reward calculations, input validation, duplicate event checks, and refund validation.

## Remaining failures or limitations

- The final recorded test run had no failing tests: `221 passed in 0.46s`.
- Refund behaviour when a customer has already spent some of their awarded points still needs a clearly defined business rule.
- The current implementation limits point reversal to the available balance. The expected behaviour for the remaining reversal amount needs further investigation.
- The exact Python interpreter version and separate output of `python -m main` were not recorded.
- No dedicated performance benchmarks were performed.