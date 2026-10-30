# REWARD_RULE_NOTES.md

## Worked points calculation
Purchase of Rs 2,500 (250,000 paise), 2 points per Rs 100, 10% bonus, cap of 60.
- base_points = floor(250000 / 10000) * 2 = 25 * 2 = 50
- bonus_points = floor(50 * 110 / 100) = 55
- cap: min(55, 60) = 55 points awarded

## Partial refund example
Refund of Rs 1,000 (100,000 paise) on that purchase.
- points to reverse = floor(55 * 100000 / 250000) = 22
- balance goes from 55 to 33, and the ledger gets an entry of -22

## Edge cases
1. 19,999 paise earns floor(1.9999) = 1 hundred, not 2 (no rounding up).
2. cap_points = 0 gives 0 points.
3. A refund larger than the remaining amount, or with a wrong type, is ignored and the account does not change.
4. The same event_id sent twice changes the balance only once.