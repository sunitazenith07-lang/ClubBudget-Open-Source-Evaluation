# Implementation Approach

Complete this file in your own words. Be concise and specific to the work you actually did.

## 1. Baseline
- Commands run before editing:
  - `python --version` (returned `Python 3.14.7`)
  - `python -m pytest -q`
  - `python -m main`
- Initial test result (include the actual summary):
  - `67 failed, 147 passed, 1 warning in 1.46s` (out of 214 total tests).
- Demo/output observed:
  - `Points example: 25`
  - `Repeat warnings: []`

## 2. Codebase understanding
- Important files/functions inspected:
  - `service.py`: Contains `calculate_points`, `apply_reward_event`, and `flag_repeat_transactions`.
  - `models.py`: Defines `new_account` which initializes the account dictionary structure.
  - `tests/test_contract.py`: Basic contract tests checking base rules like floor calculation, cap of 0, event deduplication, and refund bounds.
  - `tests/test_acceptance_matrix.py`: Large parameterized test suite checking boundaries, edge cases, type safety, and ordering.
- Rewards calculation, refund, ledger or alert flow traced:
  - Purchases: Event arrives -> check if event was already processed -> validate amount -> calculate base points using floor division per ₹100, add bonus, apply cap -> update points balance, store transaction, write ledger entry, and save event ID.
  - Refunds: Check event ID -> find transaction by ID -> validate refund amount (must be positive int and not exceed remaining amount) -> compute proportional points reversal using cumulative refunded paise -> subtract delta from account points balance without going below zero -> append ledger entry and save event ID.
  - Repeat alerts: Group transactions by `(account_id, date, amount_paise)` -> filter groups with more entries than threshold -> sort by account ID deterministically.
- How you confirmed your understanding:
  - Read through `STUDENT_PROBLEM_STATEMENT.md` and checked the exact failure tracebacks in `test_contract.py` to see where the starter code diverged from the rules.

## 3. Investigation and implementation strategy
For each major defect, describe the symptom, hypothesis, evidence from a test/log/example, and the fix chosen.
- Issue 1: Floating-point rounding used instead of floor division
  - Symptom: A purchase of 19,999 paise (₹199.99) earned 2 points instead of 1 point.
  - Hypothesis: The starter was using Python's `round(amount_paise / 10000)` which rounds up at .5 and above.
  - Evidence: `FAILED tests/test_contract.py::test_points_use_floor - assert 2 == 1`.
  - Fix: Changed the calculation to integer floor division: `(amount_paise // 10000) * points_per_100_rupees`.
- Issue 2: A cap of 0 was ignored
  - Symptom: When `cap_points=0` was passed, the starter awarded full points instead of 0.
  - Hypothesis: In Python, `0` is falsy, so `if cap_points:` evaluated to `False` and skipped the cap entirely.
  - Evidence: `FAILED tests/test_contract.py::test_cap_zero_is_respected - assert 5 == 0`.
  - Fix: Changed check to `if cap_points is not None:` and returned 0 if `cap_points <= 0`.
- Issue 3: Duplicate events awarded points multiple times and invalid refunds corrupted state
  - Symptom: Sending the same `event_id` twice awarded points twice and added duplicate ledger records. Excess or invalid refunds (like negative numbers or booleans) also modified the account.
  - Evidence: `FAILED tests/test_contract.py::test_purchase_event_once` and `FAILED tests/test_contract.py::test_invalid_or_excess_refund_ignored`.
  - Fix: Added an early check `if not event_id or event_id in out['processed_event_ids']: return out`. Added strict type checks (`type(...) is int`) and checked `refunded_paise + refund <= original_amount` before making any state changes.

## 4. Implementation decisions
- Main changes and why:
  - Kept all calculations as pure integer arithmetic (`//` and `*`) to avoid floating-point inaccuracies.
  - Used `type(x) is int` rather than `isinstance(x, int)` to prevent `True`/`False` booleans from being treated as 1/0.
  - Placed early return guards at the start of `apply_reward_event` so invalid or replay events return the unmodified account copy immediately without appending to the ledger or modifying balances.
- Alternatives considered and why rejected:
  - Using `math.floor(amount / 10000)`: Rejected because native `//` is simpler, faster, and stays purely in integers.
  - Storing `processed_event_ids` as a `set`: I thought about this for O(1) lookups, but the tests explicitly check `account['processed_event_ids'] == ['E1']` expecting an ordered list, so keeping a list was necessary for compatibility.
