# Testing Notes

| Scenario | Setup/input | Expected | Actual | Result |
|---|---|---|---|---|
| Search / points calculation | `calculate_points(19999, 1)` | `1` (floor) | `1` | Pass |
| Combined filters / bonus + cap | `calculate_points(50000, 2, 50, 6)` | `6` | `6` | Pass |
| Invalid input / negative amount | `calculate_points(-10000, 1)` | `0` | `0` | Pass |
| Domain state transition / purchase replay | Apply same purchase event twice | Balance unchanged, one event ID, one ledger entry | As expected | Pass |
| Domain state transition / refund replay | Apply same refund event twice | No duplicate reversal | As expected | Pass |
| Empty/missing data / empty transactions | `flag_repeat_transactions([], 2)` | `[]` | `[]` | Pass |
| Empty/missing data / malformed repeat input | Non-dict rows, non-numeric threshold | Safe list, no crash | Safe list, no crash | Pass |
| Invalid input / excess refund | Refund `150000` paise on `100000` paise purchase | Account unchanged | Account unchanged | Pass |

## Automated run
- Command: `python -m pytest -q`
- Total: 214
- Passed: 214
- Failed: 0
- Errors: 0
- Skipped: 0