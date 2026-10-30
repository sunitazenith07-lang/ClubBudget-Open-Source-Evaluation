# Project Notes

## Requirements completed
1. **Integer Floor Arithmetic Points Calculation:** Correctly implemented `base_points = (amount_paise // 10000) * points_per_100_rupees` and `bonus_points = (base_points * (100 + bonus_percent)) // 100`, followed by cap evaluation.
2. **Rule and Input Boundaries:** Invalid/negative amounts, negative bonus percentages, non-integer types (including Python booleans), and zero caps (`cap_points = 0`) are properly validated to produce 0 points.
3. **Capture Status Enforcement:** Only `purchase_captured` events award points; `purchase_declined`, `purchase_pending`, and unknown events are rejected.
4. **Event Idempotency:** Implemented event deduplication via `processed_event_ids`, guaranteeing that replaying purchase or refund events cannot duplicate point adjustments or ledger entries.
5. **Proportional Refund Reversals:** Implemented cumulative integer reversal `(awarded * cumulative_refund) // total_amount`, clamped to prevent over-reversal or negative account balances. Over-refunds are rejected.
6. **Audit Ledger Integrity:** Every accepted purchase or refund event writes an immutable ledger entry with `event_id`, `type`, and `points_delta`.
7. **Repeat-Transaction Alerts:** Transactions are grouped by `(account_id, date, amount_paise)` and flagged if the count exceeds the threshold. Alerts are purely informational for compliance review.
8. **Safe Input & Boundary Handling:** Empty inputs, malformed types, and missing identifiers are handled gracefully.
9. **Optional Stretch Work:** Implemented `generate_account_statement_csv` for exporting an auditable account statement with running point balances in CSV format.

## Files changed
- `service.py`: Replaced floating-point rounding with integer floor division, added strict type and value guards, fixed zero-cap handling, implemented idempotency and refund bounds validation, hardened repeat alerts, and added CSV statement generation.
- `main.py`: Updated demo execution to demonstrate points calculation, repeat warnings, event application, and CSV statement generation.
- `.gitignore`: Added `.DS_Store` to keep repository clean on macOS.
- `tests/test_regression.py`: Added 7 comprehensive regression tests covering idempotency, partial refunds, integer truncation, zero points, malformed payloads, rules safeguards, and CSV generation.
- `approach.md`, `challenges.md`, `optimizations.md`: Completed all three mandatory problem-solving documents with actual empirical evidence.
- `TESTING.md`, `TESTING_TEMPLATE.md`, `REWARD_RULE_NOTES.md`: Completed test evidence and challenge-specific domain notes.

## Decisions and assumptions
- All currency calculations operate exclusively on integers representing paise.
- Negative points balances are strictly prohibited; reversals are clamped by both awarded points and available balance.
- Event deduplication relies on string `event_id`. Events without valid string identifiers are rejected.
- Alerts do not block transactions; operations teams review alerts independently.

## Tests and results
- Baseline: `67 failed, 147 passed in 0.21s` across 214 tests.
- Final: `224 passed in 0.06s` across 224 tests (100% pass rate).


## Limitations and next steps
- The service currently operates on in-memory dictionary data structures.
- Next step for production would be persisting state to an ACID-compliant database with row-level locking or an event-sourcing append-only log.
