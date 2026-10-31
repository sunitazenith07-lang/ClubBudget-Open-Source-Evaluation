<!-- DRAFT: resolve every [VERIFY] and [FILL] marker with your own run/edits, then delete this comment. -->
# Project Notes

## Requirements completed
Against the eight rules in the problem statement:
1. Integer points formula (floor, bonus, cap last): done in `calculate_points`.
2. Invalid or negative amounts and rules give 0 points, and a cap of 0 gives 0: done.
3. Only captured purchases earn points: done.
4. Each `event_id` processed once: done, and only accepted events are recorded.
5. Proportional integer refund reversal, never more than awarded, never negative balance: done.
6. One ledger entry per accepted purchase or refund: done.
7. Repeat alerts by account, date and amount; review signals only: done; they never block or change anything.
8. Empty input, missing IDs, unknown transactions, boundary values: handled without crashes.

Stretch work: none attempted.

## Files changed
- `service.py`: all fixes.
- `tests/test_regressions.py`: new, 12 tests.
- New or completed documents: `approach.md`, `challenges.md`, `optimizations.md`, `TESTING.md`, `REWARD_RULE_NOTES.md`, `AI_USAGE.md`, `ARCHITECTURE.md`, `PROJECT_NOTES.md`.
- Not changed: `models.py`, `fixtures.py`, `main.py`, the provided tests, and the workflows.

## Decisions and assumptions
- Reject, don't clamp, an over-refund; the provided tests require this.
- Rejected events are not stored as processed, which keeps processed IDs and the ledger 1:1 and lets a corrected event be retried.
- Purchases with amount ≤ 0 are rejected, and IDs must be non-empty strings.
- The repeat alert uses `>` (pinned by the tests), and a threshold below 1 counts as 1. Records with missing account, date or amount are skipped.
- I used AI help as permitted; see `AI_USAGE.md`.

## Tests and results
- Baseline: `67 failed, 147 passed` [VERIFY].
- After fixes: `226 passed` [VERIFY], with `python -m pytest -q`. The demo prints `Points example: 27` [VERIFY].
- `records.json` check: no negative balances, ledger matches balance, no `None` IDs [VERIFY].
- CI result on my PR: [FILL].

## Limitations and next steps
- Per-event deepcopy is O(n²) over long streams (see `optimizations.md`).
- Out-of-order refunds are rejected and not queued.
- Events are not checked against their `account_id`.
- The first CI run on Python 3.11 is my only 3.11 check, since I tested locally on a different version [FILL: your Python version].
- Next: the batch `apply_events` function, then rejection reason codes.