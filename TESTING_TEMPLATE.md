# Testing Notes

| Scenario | Setup/input | Expected | Actual | Result |
|---|---|---|---|---|
| Points Floor Calculation | `amount_paise = 19999`, `points_per_100_rupees = 1` | 1 point awarded (no rounding up to 2) | 1 point awarded | PASS |
| Promotional Cap of Zero | `amount_paise = 50000`, `cap_points = 0` | 0 points awarded (cap of 0 respected) | 0 points awarded | PASS |
| Invalid / Excess Refund | Refund 150,000 paise on 100,000 paise purchase | Event ignored, transaction state unchanged | Refund ignored, balance intact | PASS |
| Domain state transition (Multi-Refund) | Sequential refunds of 40,000 and 60,000 paise on 100,000 paise purchase | Proportional deduction (4 then 6 points), final balance 0 | Reversed 10 points total, balance 0 | PASS |
| Empty/missing data | Malformed event with missing `event_id` or `transaction_id` | Unaltered account returned | Unaltered account returned | PASS |

## Automated run
- Command: `python -m pytest -q`
- Total: 219
- Passed: 219
- Failed: 0
- Errors: 0
- Skipped: 0
