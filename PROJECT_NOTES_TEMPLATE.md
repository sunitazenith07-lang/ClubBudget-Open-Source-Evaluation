# Project Notes

## Requirements completed
- Integer points calculation with bonus and cap.
- Idempotent event processing.
- Bounded proportional refunds with non-negative balances.
- Auditable ledger entries.
- Repeat-transaction alerts with threshold handling.
- Safe handling of malformed/empty inputs.

## Files changed
- `service.py`
- `approach.md`
- `challenges.md`
- `optimizations.md`
- `TESTING.md`
- `REWARD_RULE_NOTES.md`

## Decisions and assumptions
- Refund amounts are in paise and must be positive integers within remaining refundable amount.
- Invalid refund events leave the account unchanged.
- Missing identifiers are handled defensively.
- Repeat alerts are advisory only.

## Tests and results
- `python -m pytest -q` → 214 passed, 0 failed.
- `python main.py` → successful output.

## Limitations and next steps
- No persistent storage; state is in-memory.
- Documentation could be expanded with more detailed investigation notes.
- Additional property-based tests could further strengthen refund/idempotency coverage.