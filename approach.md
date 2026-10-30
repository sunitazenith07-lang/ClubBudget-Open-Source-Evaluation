# approach.md

Practice run, AI-assisted

## 1. Baseline
Commands run before making changes: python -m pytest -q and python -m main.

Initial test results: 67 failed and 147 passed out of 214 tests.

Most failures were related to purchase event replay, refund validation, points calculation, refund limits, transaction recording, and bonus calculations. There were also 4 failures in test_contract.py.

Demo output showed Points example: 28 and Repeat warnings: []. However, according to the given formula, 259900 paise should give 27 points (25 × 110 // 100), not 28. This indicated that the demo’s calculation was incorrect even before my changes.

## 2. Codebase understanding
All the main logic is in service.py, including calculate_points, apply_reward_event, and flag_repeat_transactions.

The models.new_account function defines the account structure, which includes points_balance, a list of processed_event_ids, a dictionary of transactions organised by transaction ID, and a ledger.

The general flow is that an event is passed to apply_reward_event, which first creates a deep copy of the account. For a purchase_captured event, it calculates the points and stores the transaction. For a refund_processed event, it finds the original transaction and reverses the points proportionally. Finally, it adds an entry to the ledger.

The flag_repeat_transactions function groups transactions using (account_id, date, amount_paise) and flags groups containing more entries than the given threshold.

I checked the failing test assertions and reproduced the issues in the Python shell to understand what was going wrong. For example, calculate_points(19999, 1) returned 2, which helped identify a problem with the points calculation.


## 3. Investigation and fixes
Issue 1 – Incorrect points rounding: I found that calculate_points(19999,1) was returning 2 instead of 1. This happened because round(amount/10000) used floating-point division and rounded the result up. I replaced it with amount // 10000 to ensure the calculation uses integer floor division.

Issue 2 – Zero-point cap not working: When I tested calculate_points(50000,1,cap_points=0), it returned 5 instead of 0. The problem was that if cap_points: treated zero as if no cap had been provided. I changed the condition to if cap_points is not None so that a cap of zero is also handled correctly.

Issue 3 – Invalid inputs not handled properly: The original code did not properly validate negative values, floats, strings, or booleans. Since Python treats True and False as integers, they also needed separate handling. I added an _is_int() helper to reject booleans and other invalid inputs. Invalid or negative values now return 0 points.

Issue 4 – Duplicate events being processed: When the same purchase event was replayed, its ID was added to processed_event_ids again, causing duplicate entries. I fixed this by checking whether an event ID has already been processed. If it has, the function returns an unchanged copy of the account. Only successfully accepted events are added to the processed event list.

Issue 5 – Refund validation: I found that the system allowed refunds greater than the original purchase amount. It also failed to handle invalid refund values such as negative numbers, strings, floats, booleans, and other unsupported types. I added validation to ensure that refunds must be positive integers and that the total refunded amount never exceeds the original purchase amount. Invalid refund events are rejected without changing the account.


## 4. Implementation decisions
For refunds, I used the total refunded amount instead of calculating each refund separately. The formula target = awarded * total_refunded // amount calculates how many points should be reversed so far. I then subtract the points already reversed. This avoids calculation errors when a purchase is refunded in multiple parts and ensures that a full refund reverses all the awarded points.

I also made sure that the points being reversed never exceed the account’s current balance, so the balance cannot become negative.

Events without an event_id or transaction_id are ignored because they cannot be properly tracked or linked to an existing transaction.

If a purchase is received again with a different event ID but the same transaction ID, the system does not award points a second time.

I added transaction_id and balance_after to ledger entries so that each transaction is easier to track and verify. Even if a refund reverses zero points, it still gets a ledger entry because the event itself was accepted.

For repeat transaction alerts, I added a few checks. Invalid thresholds are treated as 1, rows with missing account IDs or dates or invalid amounts are skipped, and duplicate transaction IDs within the same group are counted only once. I also kept the existing sorted output order and added review_only: True to every alert.

I considered raising exceptions for invalid inputs, but rejected that approach because the tests expected invalid events to be safely ignored. I also avoided partially processing excessive refunds. Instead, the entire refund event is rejected if it exceeds the remaining refundable amount.


## 5. Verification
I added a new file, tests/test_regressions.py, with 28 additional tests. These cover the issues I fixed, including replaying events from the complete data/records.json file and testing repeat transaction datasets.

After making all the changes, I ran the tests again using python -m pytest -q. All 242 tests passed successfully.

I also ran python -m main, which now correctly displays Points example: 27 instead of 28.                  