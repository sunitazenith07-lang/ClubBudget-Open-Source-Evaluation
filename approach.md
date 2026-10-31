## 1. Baseline

Run the following commands:

python -m pip install -r requirements-dev.txt

python -m pytest -q

python -m main

The initial tests show that 67 failed and 147 passed (214 total).

Test failures:

floor calculation: 11



bonus/cap matrix: 3

capture purchases: 6

replay purchase idempotent: 20

refund limits: 10

invalid/refund too much: 13

test_contract.py: 4

Demo result:

Points example: 28

Repeat warnings: []

## 2. Understand

Files reviewed: service.py, models.py, fixtures.py, main.py, both test files, .github/workflows/tests.yml, data/README.txt.

The function apply_reward_event makes a copy of the account. It looks at the event['type'] field. If it is a purchase, calculate_points is called and the transaction is recorded along with a row added to the ledger. If it is a refund, it will find the transacion and revert the points. flag_repeat_transactions will create groups based on account, date, and amount.

I tested this manually for the demo (I expected 27 but had 28). Parametrised tests had the expected values.

## 3. Investigate

Issue 1: Rounding. When calculate_points was used with 19999 and 1, it returned 2. round(1.9999) will round up. To fix this, replace amount_paise // 10000.

Issue 2: Cap of 0. When cap_points was set to 0 it returned 5. When using if cap_points: 0 is considered false. Instead use if cap_points is not None:.

Issue 3: Duplicate events. processed_event_ids was becoming ['E1', 'E1']. Event IDs were not being checked. Return early if the event_id has been used. Or if event_id/transaction_id is not provided.

Issue 4: Refund validation. When any of the following were provided: -1, 0, 150000, True, None, "100", 1.5 it changed refunded_paise. Only allow positive integers (not bool). Ensure that refunded_paise + refund <= amount_paise. Also ensure that it cannot go below 0.



## 4. Decide

Minimal changes have been made. Fixed the issues within the functions and created 1 helper function _is_int. This will be used for all number checks.

Refunds over the limit are not capped. The tests (test_refund_amount_bounds_and_balance) expect refunded_paise to remain 0.

Repeat check remains as len(ids) > threshold. Threshold tests have confirmed this. Rows with missing fields are skipped. None inputs have been added.

Assumptions have been made. If the bonus or cap is negative it is considered an invalid rule and points will be 0. If the refund is for a transaction that does not exist it will be ignored.



## 5. Test

Added tests in tests/test_regression.py (12 tests). 9 of these fail with the start code.

Final results: 226 passed (214 + 12). Demo now shows Points example: 27.

Limitations can be seen in TESTING.md.