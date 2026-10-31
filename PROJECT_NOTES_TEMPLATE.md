# Project notes

## Requirements completed
Four existing commits address floor/bonus/cap calculations, event replay, refund validation, and repeat-alert input handling. Added regressions and completed the five mandatory root notes. This documentation was AI-assisted; see AI_USAGE_TEMPLATE.md.

## Files changed
Existing implementation: `service.py`, `tests/test_contract.py`. Submission preparation: `approach.md`, `challenges.md`, `optimizations.md`, `TESTING.md`, `REWARD_RULE_NOTES.md`, these supporting note templates and AI declaration. The removed partial-refund assertion was restored. Requirement documents, workflow and datasets remain unchanged.

## Decisions and assumptions
Integer paise; cumulative proportional reversal; immutable caller account; exact repeat keys; strict threshold. Accounts follow `models.new_account`.

## Tests and results
Reconstructed starter at `2bc08df`: 67 failed, 147 passed. Current: 219 passed. Demo: 27 points, no warnings. See TESTING.md for reproducible commands and provenance.

## Limitations and next steps
Check PR CI separately. No benchmark, concurrency guarantee or exhaustive malformed-state validation. Original personal development history was not supplied. The integrity checklist is left for the submitter; no compliance claim is made by this preparation.
