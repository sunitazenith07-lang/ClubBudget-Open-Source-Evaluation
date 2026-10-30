# approach.md - Required submission

## 1. Baseline
- Commands run before editing: `python -m pytest -q`
- Initial test result: 173 passed, 41 failed (214 total).
- Demo/output observed: `python -m main` printed `Points example: 28` with the old rounding implementation and `Repeat warnings: []`.

## 2. Codebase understanding
- Important files/functions inspected: `models.py:new_account`, `service.py:calculate_points`, `apply_reward_event`, `flag_repeat_transactions`, tests under `tests/`, and `data/records.json` rule/edge-case catalog.
- Rewards calculation, refund, ledger or alert flow traced: purchase event calculates points, stores transaction, updates balance and ledger; refund event proportionally reverses points and appends ledger; repeat alerts group transactions by account/date/amount.
- How you confirmed your understanding: ran the baseline suite and mapped each failure to the acceptance tests and problem statement.

## 3. Investigation and implementation strategy
- Issue 1: points used `round(amount_paise / 10000)` instead of floor, causing boundary mismatches. Evidence: `test_integer_floor_points_calculation` failures such as 9999 -> 1. Fix: use `amount_paise // 10000`.
- Issue 2: bonus/cap ordering and invalid input handling were incomplete. Evidence: `test_bonus_and_cap_matrix` and rule cases in `data/records.json`. Fix: floor base, floor bonus, apply cap last, return 0 for invalid values.
- Issue 3: refunds were capped instead of ignored when excessive, and invalid refund amounts were coerced with `max(0, ...)`. Evidence: `test_refund_amount_bounds_and_balance` and `test_invalid_or_excess_refund_does_not_change_account`. Fix: validate refund type, positivity, and cumulative bounds; ignore invalid refunds without changing state.
- Issue 4: repeat-alert threshold and input handling needed defensive guards. Evidence: threshold-boundary tests. Fix: normalize invalid thresholds and skip non-dict transactions.

## 4. Implementation decisions
- Main changes and why: changed `service.py` only, preserving public function signatures and deepcopy-based immutability.
- Alternatives considered and why rejected: capping excessive refunds was rejected because acceptance tests require excess refunds to leave the account unchanged.
- Assumptions: amounts and rule values are expected to be integers; non-integer or boolean values are treated as invalid.

## 5. Verification
- Tests added or changed: no test files changed; existing 214 tests used as the acceptance contract.
- Commands run and actual results: `python -m pytest -q` -> `214 passed in 0.13s`; `python -m main` -> `Points example: 27`.
- Edge cases verified: floor boundaries, bonus/cap, invalid amounts/rules, idempotent replay, partial/excess refunds, repeat threshold boundaries, distinct keys, non-mutation.
- Remaining failures or known limitations: none for the visible suite.