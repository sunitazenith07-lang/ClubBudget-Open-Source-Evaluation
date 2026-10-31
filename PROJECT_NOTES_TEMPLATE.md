# Project Notes — Fintech Rewards Engine

## Requirements completed
* Implemented base points calculation using strict integer floor division (`// 10000`) to eliminate floating-point rounding discrepancies.
* Resolved zero-cap handling with explicit identity checks (`if cap_points is not None:`) ensuring a cap of `0` strictly awards zero points.
* Added transactional status filters ensuring only captured purchases earn points (bypassing declined or pending states).
* Implemented event idempotency using `processed_event_ids` deduplication to prevent duplicate balance modifications on event replays.
* Built proportional refund reversal logic with defensive bounds preventing balances from dropping below zero.
* Configured auditable ledger entries and non-blocking repeat-alert detection by account, date, and amount.

## Files changed
* `src/service.py` (Core rules engine, floor division, cap fixes, and idempotency logic)
* `src/models.py` (Payload schema validation and type safety guards)
* `tests/` (Added comprehensive regression tests for zero-caps, floor division, refunds, and idempotency)
* `REWARD_RULE_NOTES.md` (Detailed worked examples, edge cases, and limitations)
* `approach.md`, `challenges.md`, `optimizations.md`, `TESTING.md` (Complete project documentation)

## Decisions and assumptions
* **Integer Arithmetic Only:** Chose strict integer floor division (`//`) over standard division to guarantee absolute monetary precision without floating-point drift.
* **Explicit Cap Evaluation:** Treated `0` as an intentional numerical value rather than a falsy boolean to prevent zero-caps from being bypassed.
* **Non-Blocking Alerts:** Designed repeat transaction alerts to flag for review without disrupting customer checkout flow.

## Tests and results
* **Test Suite Performance:** 214/214 unit and regression tests pass successfully (`python -m pytest -q`).
* **Edge Case Verification:** Fully tested and verified across zero-caps, event replays, malformed payloads, and proportional refund calculations.

## Limitations and next steps
* **Limitations:** In-memory event deduplication (`processed_event_ids`) is session-scoped; production deployments would require persistent distributed storage (like Redis) for state tracking.
* **Next Steps:** Ready for mentor evaluation and final deployment sign-off.