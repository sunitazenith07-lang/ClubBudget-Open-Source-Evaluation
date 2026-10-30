# Testing Notes

| Scenario | Setup/input | Expected | Actual | Result |
|---|---|---|---|---|
| Search & Floor Points | `amount_paise = 19999`, `points_per_100_rupees = 1` | 1 point awarded (floor) | 1 point awarded | Passed |
| Bonus & Cap Rules | `amount = 50000`, `points_per_100_rupees = 2`, `bonus = 50%`, `cap = 6` | 6 points awarded (capped) | 6 points awarded | Passed |
| Zero Cap Boundary | `amount = 50000`, `cap = 0` | 0 points awarded | 0 points awarded | Passed |
| Invalid input | Negative amount, string amount, boolean amount | 0 points awarded / event rejected | 0 points awarded / rejected | Passed |
| Domain state transition | Replay `purchase_captured` or `refund_processed` event | Idempotent; no duplicate ledger or balance change | Balance unchanged, 1 ledger entry | Passed |
| Proportional Refund | Sequential partial refunds (50% then 50%) on 15 pt purchase | Reverses 7 then 8 pts, ending at 0 balance | 7 then 8 pts reversed, 0 balance | Passed |
| Excess Refund | Refund amount exceeding purchase amount | Rejected; account unchanged | Account unchanged | Passed |
| Repeat Detection | 3 transactions with identical account, date, amount; threshold = 2 | Grouped and flagged in alert list | Flagged in alert list | Passed |

## Automated run
- Command: `python -m pytest -q`
- Total: 221
- Passed: 221
- Failed: 0
- Errors: 0
- Skipped: 0

