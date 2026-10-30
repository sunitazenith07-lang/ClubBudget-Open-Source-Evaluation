# approach.md - Required submission

Complete this file in your own words. Be concise and specific to the work you actually performed.

## 1. Baseline
Commands run before editing: python --version, python -m pip install -r requirements-dev.txt, python -m pytest -q against the starter service.py from Git HEAD.
Initial test result (include the actual summary): 67 failed, 147 passed (214 tests total) in 0.18s. Failures were concentrated around rounding errors on fractional ₹100 boundaries, ignoring zero-caps (cap_points = 0), duplicate event processing, and invalid/excessive refund calculations.
Demo/output observed: Running python -m main printed:
Points example: 27
Repeat warnings: [] (Transactions in sample fixtures had only 2 repeats for ACCT-1001, which did not strictly exceed the default threshold of 2).
## 2. Codebase understanding
Important files/functions inspected:
service.py: Contains calculate_points(...), apply_reward_event(...), and flag_repeat_transactions(...).
models.py: Contains new_account(account_id) initializing points_balance, processed_event_ids, transactions, and ledger.
fixtures.py: Provides baseline test data (sample_account, sample_transactions, sample_rules).
main.py: Entry point running the sample points calculation and repeat-detection demo.
tests/test_contract.py & tests/test_acceptance_matrix.py: Acceptance suites asserting arithmetic, edge cases, and idempotency contracts.
Rewards calculation, refund, ledger or alert flow traced:
calculate_points: Converts purchase paise into base loyalty points per ₹100, applies promotional bonus percentages using integer math, and caps points if a cap is provided.
apply_reward_event: Immutably clones the account dictionary via deepcopy. Rejects duplicates if event_id is in processed_event_ids. For purchase_captured, awards points, updates account balance, stores transaction details, and appends a positive ledger delta. For refund_processed, validates refund limits, reverses points proportionally, updates balance, and appends a negative ledger delta.
flag_repeat_transactions: Groups transactions by (account_id, date, amount_paise) tuple key and returns groups where count strictly exceeds threshold.
How understanding was confirmed:
Traced failing test assertions in tests/test_acceptance_matrix.py.
Inspected the diff between Git HEAD and expected business rules in STUDENT_PROBLEM_STATEMENT.md.
Ran pytest after each atomic fix to verify progress.

## 3. Investigation and implementation strategy
Issue 1: Premature Rounding and Floating-Point Inaccuracies

Symptom: Purchases near ₹100 boundaries (e.g., ₹199.90 or 19,990 paise) awarded 2 base units instead of 1.
Hypothesis: Starter used round(amount_paise / 10000), which rounds to nearest rather than computing the floor.
Evidence: Tests expecting ₹199 to yield 1 base unit failed with 2.
Fix: Switched to floor integer division: base = (amount_paise // 10000) * points_per_100_rupees and points = base * (100 + bonus_percent) // 100.

Issue 2: Zero-Cap Bypass (Falsy Zero Bug)

Symptom: When cap_points = 0, the cap was completely ignored and full points were awarded.
Hypothesis: Starter checked if cap_points:, which treats integer 0 as falsy in Python.
Evidence: Boundary tests with cap_points=0 returned positive points.
Fix: Changed condition to explicitly check for None: if cap_points is not None: points = min(points, cap_points).

Issue 3: Missing Idempotency & Replay Vulnerability

Symptom: Processing the same event_id multiple times credited or debited points repeatedly.
Hypothesis: apply_reward_event did not inspect account['processed_event_ids'] before applying mutations.
Evidence: Duplicate event tests failed with doubled balances and duplicate ledger rows.
Fix: Added guard at top of function: if not event_id or event_id in out['processed_event_ids']: return out. Also ensured event_id is only appended to processed_event_ids if the event is valid and accepted.

Issue 4: Unbounded & Cumulative Refund Calculations

Symptom: Excessive refunds were processed, negative/zero refunds mutated state, and sequential partial refunds suffered rounding drift.
Hypothesis: Starter lacked boundary validation and computed reversal per isolated event rather than cumulatively against transaction history.
Evidence: Negative points balance occurred on excess refunds; sequential partial refunds drifted from expected proportional total.
Fix: Added strict checks (type(refund) is int, refund > 0, and txn['refunded_paise'] + refund <= txn['amount_paise']). Calculated cumulative reversal: should_reverse = txn['awarded_points'] * txn['refunded_paise'] // txn['amount_paise'], setting delta = should_reverse - txn['reversed_points'].

## 4. Implementation decisions
Main changes and why:
Enforced strict type guards (type(...) is not int) across all numeric inputs to prevent boolean values (True/False) or invalid strings/floats from corrupting ledger arithmetic.
Used pure integer arithmetic (//) throughout to eliminate floating-point drift and guarantee exact reproducibility across platforms.
Handled unrecognized or invalid events by returning the account unchanged without appending their event_id to processed_event_ids.
Alternatives considered and why rejected:
Decimal module: Rejected because problem specification explicitly calls for standard integer arithmetic in paise.
Exception raising for invalid events: Rejected because streaming event processors must be resilient and return the unchanged account state rather than crashing the worker pipeline.
Assumptions:
Currency inputs are always denominated in paise (
1
 Rupee
=
100
 paise
1 Rupee=100 paise).
Alerts from flag_repeat_transactions are purely advisory for human review and should never mutate account state or block processing.

## 5. Verification
Tests added or changed:
Kept existing test suites (tests/test_contract.py and tests/test_acceptance_matrix.py) intact without deleting, weakening, or skipping tests.
Commands run and actual results:
python -m pytest -q: Resulted in 214 passed in 0.15s.
python -m main: Successfully printed Points example: 27 and Repeat warnings: [].
Edge cases verified:
Paise boundaries (₹99.99 earns 0 points, ₹100.00 earns 1 base unit).
Explicit zero cap (cap_points = 0) correctly returns 0 points.
Negative purchase amounts, negative bonus percentages, and negative caps return 0.
Duplicate event_id replays produce no change in balance or ledger.
Full and partial refunds reverse exact proportional points without going negative.
Refunds exceeding the original transaction amount are rejected.
Refunds against non-existent transactions are ignored.
Remaining failures or known limitations:
None. All 214 tests pass cleanly.