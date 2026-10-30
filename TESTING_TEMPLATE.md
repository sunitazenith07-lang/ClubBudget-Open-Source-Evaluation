# Testing Notes

| Scenario | Setup/input | Expected | Actual | Result |
|---|---|---|---|---|
| Search / Alert grouping | Grouping 3 transactions for account 'A' on date 'D' with amount 1000 paise with threshold 2 | 1 alert flagged containing all 3 transaction IDs | Flagged 1 group with IDs `['0', '1', '2']` | Pass |
| Combined filters / Rules matrix | 50,000 paise, 2 pts per 100 rupees, 50% bonus, cap 6 points | Base = 10, bonus = 15, capped at 6 | Output = 6 | Pass |
| Invalid input | Negative purchase amount `-10000` paise, boolean refund amount `True`, or negative cap `-5` | 0 points awarded, invalid refund rejected, account unchanged | Balance unchanged, 0 points generated | Pass |
| Domain state transition | Captured purchase of 100,000 paise (10 pts) followed by 50,000 paise partial refund | Balance drops from 10 to 5; transaction records 5 pts reversed | Points balance = 5, reversed_points = 5 | Pass |
| Empty/missing data | Event missing `event_id` or `transaction_id`, or non-dict account input | Handled gracefully without crash or ledger corruption | Default clean account returned without side effects | Pass |

## Automated run
- Command: `python -m pytest -q`
- Total: 224
- Passed: 224
- Failed: 0
- Errors: 0
- Skipped: 0

