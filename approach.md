approach.md - Required submission

I am a first-year student who just finished learning the basics of Python. Here is how I approached and fixed the issues in the project.

1. Baseline

Commands run before editing:
- python -m pip install -r requirements-dev.txt
- python -m pytest -q
- python -m main

Initial test result (include the actual summary):
- 92 failed, 109 passed out of 201 total test cases across tests/test_contract.py and tests/test_acceptance_matrix.py.

Demo/output observed:
- Running python -m main printed:
  - Points example: 28
  - Repeat warnings: [{'account_id': 'ACCT-1001', 'date': '2026-10-21', 'amount_paise': 259900, 'transaction_ids': ['TX-1', 'TX-2']}]

2. Codebase understanding

Important files/functions inspected:
- models.py: Defines new_account(account_id) which returns a dictionary with account_id, points_balance, processed_event_ids, transactions, and ledger.
- service.py: Contains the three core functions: calculate_points, apply_reward_event, and flag_repeat_transactions.
- fixtures.py and main.py: Provide sample rules and transactions and run a quick console check.
- tests/test_contract.py and tests/test_acceptance_matrix.py: Test suites checking all boundary conditions and requirements.

Rewards calculation, refund, ledger or alert flow traced:
- calculate_points converts paise to ₹100 blocks, multiplies by points_per_100_rupees, applies bonus_percent, and caps at cap_points.
- apply_reward_event copies the input account dictionary, checks the event type (purchase_captured or refund_processed), updates points_balance and transactions[txn_id], appends an entry to ledger, and records event_id in processed_event_ids.
- flag_repeat_transactions groups transactions by (account_id, date, amount_paise) and returns groups whose count exceeds threshold.

How you confirmed your understanding:
- I compared each requirement in STUDENT_PROBLEM_STATEMENT.md against the failing assertions in tests/test_contract.py and tests/test_acceptance_matrix.py.

3. Investigation and implementation strategy

Issue 1: Incorrect points calculation and cap_points=0 failure in calculate_points

- Symptom: test_points_use_floor failed because calculate_points(19999, 1) returned 2 instead of 1, and test_cap_zero_is_respected failed because calculate_points(50000, 1, cap_points=0) returned 5 instead of 0.
- Hypothesis: round(amount_paise / 10000) uses floating-point rounding instead of integer floor division, and if cap_points: treats 0 as falsy in Python.
- Evidence: In main.py, 259900 paise gave 28 points instead of 27.
- Fix chosen: Changed base calculation to (amount_paise // 10000) * points_per_100_rupees, checked if cap_points is not None, and returned 0 for non-positive or non-integer inputs.

Issue 2: Missing duplicate-event check and unsafe refund handling in apply_reward_event

- Symptom: test_purchase_event_once failed because processed_event_ids became ['E1', 'E1'], test_invalid_or_excess_refund_ignored failed on -1 and 150000, and passing rules=[] or amount=None raised AttributeError or TypeError.
- Hypothesis: apply_reward_event appended event_id at the end without checking if event_id was already in out['processed_event_ids'], and the refund branch did not check whether refund was a positive integer within the remaining refundable amount.
- Evidence: test_purchase_event_replay_is_idempotent and test_invalid_or_excess_refund_does_not_change_account failed in tests/test_acceptance_matrix.py.
- Fix chosen: Added an early return if not event_id or event_id in out['processed_event_ids'], validated isinstance(rules, dict), validated that refund is a positive integer where txn['refunded_paise'] + refund <= txn['amount_paise'], and clamped delta so reversed points never exceed awarded_points or points_balance.

Issue 3: Repeat-transaction alert threshold and invalid row filtering in flag_repeat_transactions

- Symptom: test_repeat_alert_respects_threshold[2], test_repeat_alert_threshold_boundaries, and test_repeat_alerts_do_not_mix_distinct_keys failed.
- Hypothesis: The starter code used len(ids) >= threshold instead of len(ids) > threshold and did not skip transactions with missing (None) or non-positive amounts or invalid threshold values.
- Evidence: test_repeat_alert_threshold_boundaries creates threshold matching rows and asserts flag_repeat_transactions(rows, threshold=threshold) == [], then appends one more row (threshold + 1 rows) and asserts len == 1.
- Fix chosen: Validated threshold >= 1, skipped transactions missing account_id, date, transaction_id, or positive integer amount_paise, and filtered groups with len(ids) > threshold.

4. Implementation decisions

Main changes and why:
- Added a small helper is_valid_int(value) (isinstance(value, int) and not isinstance(value, bool)) in service.py because in Python bool is a subclass of int, and the test matrix passes True and False as invalid amounts.
- Kept all data structures as simple dictionaries and lists as used in the starter code.

Alternatives considered and why rejected:
- I considered using math.floor(amount_paise / 10000), but floating-point division can lose precision on very large integers, so integer floor division // is simpler and exact.

Assumptions:
- Only valid accepted events (purchase_captured and valid refund_processed) should be added to processed_event_ids and ledger.

5. Verification

Tests added or changed:
- Added 4 regression tests to tests/test_contract.py: test_multiple_partial_refunds_cumulative_reversal, test_refund_event_replay_is_idempotent, test_cumulative_refund_exceeding_purchase_ignored, and test_missing_identifiers_and_empty_inputs_handled_safely.

Commands run and actual results:
- python -m pytest -q -> 205 passed
- python -m main -> Points example: 27 and Repeat warnings: []

Edge cases verified:
- Floor rounding at 9999 and 19999 paise, cap_points=0, negative rules/amounts, boolean/None/string amounts, duplicate purchases and refunds, multi-step partial refunds, and repeat-alert threshold boundaries.

Remaining failures or known limitations:
- No remaining test failures.