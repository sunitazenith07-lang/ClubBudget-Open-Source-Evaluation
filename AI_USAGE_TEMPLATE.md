# AI-Use Declaration

## Tools / models / sources used
- **AI coding assistant (Cline, in-editor)** — used to inspect the repository structure, read tests and data, propose edits to `service.py`, and run the pytest suite.
- **Python 3.14.8 / pytest** — used to execute and verify the test suite (`python -m pytest -q`).
- **Repository files as source of truth** — `STUDENT_PROBLEM_STATEMENT.md`, `tests/`, `data/records.json`, `fixtures.py`, `models.py`.

## Why AI was used
To accelerate codebase navigation and drafting of defensive input guards while keeping the implementation aligned with the integer-arithmetic requirements and the existing 214-test acceptance contract.

## What was independently verified or changed
- Verified the baseline result (`173 passed, 41 failed`) and final result (`214 passed`) by running the suite myself.
- Manually checked `calculate_points` against the required formula (floor base, floor bonus, cap last) and the rule cases in `data/records.json` (including `bonus_percent=-100`, negative `cap_points`, zero `cap_points`).
- Manually traced refund proportionality (`should_reverse = awarded * refunded // amount`) and cumulative-refund behaviour.
- Reviewed every edit to `service.py` for root cause rather than fixture-specific hard-coding; no test files were modified.

## Credits / tokens
- Not available (no usage meter exposed in this environment).

## One suggestion: accepted / modified / rejected
- **Accepted:** use `amount_paise // 10000` for floor division instead of `round(amount_paise / 10000)` — directly matches the required integer formula and the boundary tests.
- **Rejected:** capping an excessive refund to the transaction amount — acceptance tests require an over-limit refund to leave the account completely unchanged (`refunded_paise == 0`, balance unchanged, no ledger entry).
- **Modified:** strict refund validation was adjusted so invalid/excessive refunds are ignored (no state mutation) while still being marked processed for idempotency.

## Integrity note
No secrets or private personal data are included. All reported test results were actually run in this repository.
