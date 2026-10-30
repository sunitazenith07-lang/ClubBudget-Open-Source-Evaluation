# approach.md

## 1. Baseline
- Commands run before editing: `python3 -m pytest -q` and
  `python3 -m main`.
- Initial test result: `67 failed, 147 passed in 0.35s`.
- The initial failures covered floor-boundary calculations, zero caps,
  replayed purchases, and invalid or excessive refunds.
- The demo printed `Points example: 27` and `Repeat warnings: []`.

## 2. Codebase understanding
- Important files inspected: `service.py`, `models.py`, `fixtures.py`,
  `main.py`, both test modules, and the project instructions.
- The main flow is `calculate_points` for points arithmetic and
  `apply_reward_event` for purchases, refunds, balances, transactions,
  processed event IDs, and ledger entries. `flag_repeat_transactions`
  groups transactions by account, date, and amount.
- I confirmed the behavior by reading the assertions, reproducing failing
  inputs with focused Python calls, and rerunning the full suite after each
  implementation stage.

## 3. Investigation and implementation strategy
For each major defect, describe the symptom, hypothesis, evidence from a test/log/example, and the fix chosen.
- Issue 1: The calculation used `round(amount_paise / 10000)`, so
  `calculate_points(19999, 1)` returned `2` instead of `1`. I replaced it
  with integer floor division and kept the bonus and cap calculations in
  integer arithmetic.
- Issue 2: `if cap_points:` ignored a valid zero cap. I changed the check to
  `cap_points is not None`, so zero now produces zero points.
- Issue 3: Replayed events were not rejected, and refund amounts were
  accepted without validation. I added an early processed-event check,
  validated purchase and refund values, and limited refunds to the remaining
  refundable amount.

## 4. Implementation decisions
- Main changes: validate inputs at the calculation and event boundaries,
  use integer floor division, honor zero caps, reject duplicate event IDs,
  and calculate valid refund reversals proportionally.
- I rejected floating-point currency conversion because paise arithmetic
  can be exact with integer division. I also kept the existing dictionary
  account shape instead of introducing a new model or persistence layer,
  because the current callers and exercise are in-memory.
- Amounts and rule values are non-negative integers. Only captured
  purchases award points, and event replay protection applies to the
  supplied in-memory account state.

## 5. Verification
- Tests added or changed: no test files were changed; the existing contract
  and acceptance tests were used as regression coverage.
- Commands run: `python3 -m pytest -q` returned `214 passed in 0.08s`;
  `python3 -m main` printed `Points example: 27` and
  `Repeat warnings: []`.
- Verified cases include partial ₹100 amounts, a zero cap, invalid rule
  values, declined/pending/unknown events, duplicate purchases, valid
  partial refunds, and invalid or excessive refunds.
- No local test failures remain. Durable persistence, concurrent processing,
  and cross-process idempotency are outside the in-memory exercise.

Record actual engineering decisions and evidence. Do not claim tests or experiments you did not run.