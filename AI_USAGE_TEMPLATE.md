<!-- DRAFT: resolve every [VERIFY] and [FILL] marker with your own run/edits, then delete this comment. -->
# AI-Use Declaration

- **Tool/model:** Claude Sonnet 5.5 (Anthropic), used through claude.ai in a project containing the repository files.
- **Authorisation:** [FILL: where the organiser announced that AI is allowed, with date and link or screenshot reference]. The repository documents still contain the older no-AI wording.
- **Why I used it:** to explain the problem statement, to trace the failing tests to root causes in `service.py`, to draft the fix and the regression tests, and to draft these notes from the real results.
- **Credits/tokens displayed:** not available.
- **What I verified or changed myself:** [FILL: e.g. re-ran the baseline and the full suite locally, traced each of the 12 fixes to its failing test, ran `records.json` through the service, edited these notes]. The AI also ran the tests in its own sandbox, so I reran everything on my machine before relying on any number.
- **Suggestions:**
  - **Rejected:** the AI first suggested changing the repeat-alert comparison from `>` to `>=`. I checked the tests, saw they pin `>`, and kept it.
  - **Accepted:** floor division and `cap_points is not None`.
  - **Modified:** [FILL: one thing you changed from the AI's draft, if any]