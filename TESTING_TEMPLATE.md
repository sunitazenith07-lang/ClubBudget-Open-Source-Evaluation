# Testing Notes — RewardBook

| Scenario | Setup/input | Expected | Actual | Result |
|---|---|---|---|---|
| Search | `flag_repeat_transactions` with 3 identical transactions for account `"ACCT-1"`, date `"2026-10-21"`, amount `259900` paise, `threshold=2` | Identifies 1 repeat alert group containing all 3 matching transaction IDs | 1 alert group flagged with `transaction_ids=['TX-1', 'TX-2', 'TX-3']` | PASS |
| Combined filters | `calculate_points(50000, points_per_100_rupees=2, bonus_percent=50, cap_points=6)` | Base: `5 * 2 = 10`; Bonus: `10 * 150 // 100 = 15`; Cap: `min(15, 6) = 6` | `6` points awarded | PASS |
| Invalid input | Non-integers (`True`, `100.5`, `"10000"`), negative amounts (`-10000`), and excess refunds (`150000` paise on a `100000` purchase) | 0 points awarded for invalid amounts/rules; excess refund rejected leaving balance and transaction unmutated | `0` points awarded; excess refund safely discarded with `refunded_paise=0` and balance unchanged | PASS |
| Domain state transition | Multi-step lifecycle: Capture purchase of 100,000 paise (10 pts) -> 40,000 paise refund (4 pts) -> 60,000 paise refund (6 pts) | Balance transitions: `10 -> 6 -> 0`; cumulative `reversed_points = 10`; ledger records entries with signed deltas `[+10, -4, -6]` | `points_balance = 0`, `reversed_points = 10`, `refunded_paise = 100000`, ledger delta sum equals 0 | PASS |
| Empty/missing data | Account with `None` values (`points_balance: None`, `processed_event_ids: None`), event missing `event_id`, or `type="purchase_pending"` | Account safely sanitized without `TypeError`; invalid/pending events discarded with zero balance change and no ledger entries | Account defaults restored cleanly; 0 points awarded; ledger remains empty | PASS |

## Automated run
- Command: `python -m pytest -q`
- Total: 229
- Passed: 229
- Failed: 0
- Errors: 0
- Skipped: 0
