# Project Notes

## Requirements completed
- **Points Calculation:** Implemented integer arithmetic (`amount_paise // 10000 * points_per_100_rupees`), bonus formula, and explicit zero cap handling (`cap_points=0` returns 0).
- **Rule & Amount Validation:** Invalid, negative, zero-cap, and malformed (boolean, non-integer) inputs award 0 points.
- **Event Idempotency:** Early-return check against `processed_event_ids` prevents replayed purchases and refunds from modifying balances or duplicating ledger entries.
- **Proportional Refund Reversal:** Proportional integer reversal computed against cumulative refunded paise, eliminating integer drift across sequential partial refunds.
- **Balance Non-Negativity:** Balance strictly clamped to non-negative values; reversals cannot reduce points balance below zero.
- **Auditable Ledger:** Ledger entries (`points_delta`) accurately recorded for each accepted purchase and refund event.
- **Repeat Transaction Alerts:** Grouped by `(account_id, date, amount_paise)` above configurable threshold with deterministic sorting.
- **Stretch Feature:** Implemented `generate_account_statement_csv(account)` to output CSV statements from ledger records.

## Files changed
- `service.py`: Fixed `calculate_points`, `apply_reward_event`, and added `generate_account_statement_csv`.
- `tests/test_regression.py`: Added 7 comprehensive regression and synthetic dataset integration tests.
- `approach.md`: Completed baseline, architecture understanding, root cause analysis, decisions, and verification.
- `challenges.md`: Completed compulsory challenge report on integer refund drift and boolean type handling.
- `optimizations.md`: Completed performance analysis, trade-offs, and optimization benchmarks.
- `TESTING.md`: Documented test environment (Python 3.14.6), test results (221 passed), and 6 edge cases.
- `REWARD_RULE_NOTES.md`: Documented worked points calculation, partial refund example, and edge cases.

## Decisions and assumptions
- All monetary and points calculations use native CPython integer floor division (`//`) to eliminate binary float errors.
- Deep copying input accounts ensures pure functional behavior without in-place mutation of caller objects.
- Repeat alerts are informational for human review; transactions are never blocked automatically.

## Tests and results
- Baseline: `67 failed, 147 passed in 0.84s` (Total: 214 tests).
- Final: `221 passed in 0.16s` (Total: 221 tests, 0 failed, 0 errors, 0 skipped).
- Demo: `python -m main` runs cleanly (`Points example: 27`, `Repeat warnings: []`).

## Limitations and next steps
- Current implementation uses in-memory dictionary state; persistence to relational database (PostgreSQL) is the recommended next step for production.
- Repeat alert threshold could be wired to an external configuration service or dynamic environment variables.

