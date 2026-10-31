# AI-use declaration

AI assistance was used with evaluator permission, as confirmed by the requester on 2026-10-31. This declaration records the assistance used and does not claim independent authorship.

- Tool/source: AI assistant using Copilot SDK in VS Code. Model/version and usage credits were not available in this session.
- Purpose: inspect the repository and tests, change reward-service behavior, add regression tests, write the required documentation, and run checks.
- Verification in this session: `python -m pytest -q` completed with 221 passed; `python -m main` printed `Points example: 27` and `Repeat warnings: []`; `git diff --check` passed. The baseline result recorded in `TESTING.md` predates the current changes and was not re-run as a baseline.
- Independent human verification or edits: none were reported, so none are claimed here.
- Suggestion accepted: use integer division for floor-based points and proportional refunds, matching the requirements and tests.
- Suggestion modified: preserve `group_size > threshold` semantics at threshold zero, and add a regression test for that behavior.
