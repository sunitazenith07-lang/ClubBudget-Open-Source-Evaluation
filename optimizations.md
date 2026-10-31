# approach.md



## 1. Baseline

Commands run:

python -m pip install -r requirements-dev.txt

python -m pytest -q

python -m main

Initial results:

67 failed and 147 tests passed (Total tests = 214)

Failed tests:

floor (11),



bonus_cap_matrix (3),

capture_purchase_records (6),

replay_purchase_idempotent (20),

refund_amount_bounds (10),

invalid_refund_amount (13),

test_contract.py (4).

Demo Output:

Points example: 28

Repeat warnings: []

## 2. Understanding

Reviewed files:

service.py,

models.py,

fixtures.py,

main.py,

test files,

.github/workflows/tests.yml

data/README.txt

The apply_reward_event function clones the account. Then checks what type of reward the event is. If its a purchase then it runs calculate_points(), stores the transaction details and creates a ledger entry. If its a refund then it searches for the transaction and subtracts the appropriate amount of points. The flag_repeat_transactions function groups entries by account, date and amount.

I worked out how the demo would work manually (Expected 27, received 28). And looked at the expected values from the parametrized tests.

## 3. Investigation

Issue 1: Rounding. calculate_points(19999, 1) returns 2. round(1.9999) will round up. So we can just do integer division of amount_paise by 10000.

Issue 2: Cap of 0. If cap_points = 0 then it returns 5. Because 0 is seen as false in the if statement. So we can change it to if cap_points is not None:

Issue 3: Duplicate events. processed_event_ids becomes ['E1', 'E1']. No check was done to see if the event ids were stored. So we can add a return if the event has been processed before. Also return if there is no event_id or transaction_id.

Issue 4: Refunds. Any value less than 0 (e.g -1, 0, 150000), True, None, "100", 1.5 changed refunded_paise. We can only allow positive integers (not bool). Checked using isinstance. Also make sure that refunded_paise + refund doesn’t exceed amount_paise. Also ensure that the refunded amount doesn’t go below 0.



## 4. Implementation

I made minimal changes to the code. I fixed each bug within the functions and didn’t create any new functions. Each bug has a comment saying # BUG n fix to make it easy to locate.

I don’t cap the refund amount. I reject any over refunds. The tests (test_refund_amount_bounds_and_balance) expect the refunded_paise to remain as 0.

I left the repeat check as len(ids) > threshold. This is confirmed with the threshold tests. I also added a check to skip any rows with missing fields. Also added a check for None inputs.

Assumptions: If the bonus is negative or the cap is negative then this is an invalid rule and returns 0 points. If the refund is for a transaction that isn’t recognised then it will be ignored.



## 5. Testing

 9 tests fail with the starter code.

Final results: 214 tests passed .

Limitations: See TESTING.md.