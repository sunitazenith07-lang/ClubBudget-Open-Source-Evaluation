# Reward Rule Notes

## 1. Worked points calculation
For a captured purchase of **259,900 paise**, with 1 point per 100 rupees, a 10% bonus, and a 100-point cap:

- Base: `(259900 // 10000) * 1 = 25` points.
- Bonus: `(25 * (100 + 10)) // 100 = 27` points. The fractional result is floored using integer division.
- Cap: `min(27, 100) = 27` points.
- Observed demo output after the fix: `Points example: 27`.

## 2. Partial-refund example
A captured purchase of 100,000 paise awards 10 points. A refund of 25,000 paise gives a cumulative target reversal of `(10 * 25000) // 100000 = 2` points. The balance changes from 10 to 8. The verified refund ledger entry is:

```python
{
	'event_id': 'R',
	'transaction_id': 'T',
	'account_id': 'A',
	'type': 'refund_processed',
	'amount_paise': 25000,
	'points_delta': -2,
	'balance_after': 8,
}
```

This is asserted by `test_refund_replay_and_ledger_are_idempotent`; replaying event `R` leaves the balance, refund total, and ledger unchanged.

## 3. Edge cases
1. **Below a points boundary:** `19999` paise at 1 point per 100 rupees returns 1, not 2. Verified by `test_integer_floor_points_calculation`.
2. **Zero cap:** 50,000 paise with `cap_points=0` returns 0. Verified by `test_cap_zero_is_respected`.
3. **Over-refund:** after refunding 20,000 paise from a 30,000-paise purchase, a further 10,001-paise refund is rejected; cumulative refunded paise remains 20,000 and the balance remains 1. Verified by `test_multiple_partial_refunds_round_cumulatively_and_respect_original_amount`.

## 4. Assumptions and limitations
- Amounts and reward-rule values must be non-negative integers; booleans, fractions, strings, containers, and negative values are invalid. A zero cap is valid and awards zero points.
- Base points and bonus points both use integer floor division. Cumulative refund reversal uses the cumulative refunded amount, preventing each partial refund from independently losing fractional progress. Refunds must be positive and cannot exceed the remaining purchase amount.
- Missing or blank event/transaction identifiers prevent that event from being applied. Repeat alerts require account, date, amount, and transaction identifiers; alerts are candidate groups for human review, not a conclusion about intent.
- The implementation stores state in memory and does not provide durable processing across restarts.
