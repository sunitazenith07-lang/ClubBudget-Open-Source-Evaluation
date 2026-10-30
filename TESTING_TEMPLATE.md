# Testing Notes

| Scenario | Setup/input | Expected | Actual | Result |
|---|---|---|---|---|
| Search | `flag_repeat_transactions` on the 180 transactions in `data/records.json` with `threshold=2` | Finds 60 repeat groups where the same account, date, and amount appear more than 2 times | `len(alerts) == 60` | PASS |
| Combined filters | `flag_repeat_transactions` checking `(account_id, date, amount_paise)`, `status == "CAPTURED"`, and unique `transaction_id` | Different accounts/dates/amounts, non-captured transactions, and duplicate `transaction_id`s are not flagged | Returns `[]` | PASS |
| Invalid input | `test_invalid_or_excess_refund_does_not_change_account` across all 15 invalid inputs (`0, -1, -50, -1000, 100001, 150000, 200000, 999999, True, None, "100", 1.5, [], {}, False`) plus 10 excess inputs in `test_refund_amount_bounds_and_balance` | Returns `0` points and ignores bad refunds without changing `refunded_paise` or `points_balance` | `refunded_paise == 0` and `points_balance == 10` across all 15 inputs | PASS |
| Domain state transition | Purchase `E1` (`100000` paise -> `10` pts) -> refund `E2` (`30000` paise -> `-3` pts) -> replay `E2` (ignored) -> refund `E3` (`70000` paise -> `-7` pts) -> excess refund `E4` (`1` paisa -> ignored) | Balance goes `0 -> 10 -> 7 -> 7 -> 0 -> 0` and ledger has 3 entries summing to `0` | `points_balance == 0`, `reversed_points == 10`, `len(ledger) == 3` | PASS |
| Empty/missing data | `flag_repeat_transactions([], 2)`, `flag_repeat_transactions(None, 2)`, and events missing `event_id` or `transaction_id` | Returns `[]` or unchanged account dict without crashing | `[]` and `points_balance == 0` | PASS |

## Automated run
- Command: `py -m pytest -q`
- Total: 218
- Passed: 218
- Failed: 0
- Errors: 0
- Skipped: 0
