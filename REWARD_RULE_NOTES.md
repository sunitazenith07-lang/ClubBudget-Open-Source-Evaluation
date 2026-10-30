# REWARD_RULE_NOTES.md

## 1. Worked points calculation
For a purchase of 259900 paise (₹2,599), using points_per_100_rupees=1, bonus_percent=10, and cap_points=100, the calculation works as follows:

Base points: 259900 // 10000 = 25. The remaining ₹99 does not count, so the base points are 25.

Bonus: 25 * 110 // 100 = 27. After applying the 10% bonus, the result is 27 points.

Cap: min(27, 100) = 27. The cap does not affect the result.

I verified this by running python -m main. It now correctly displays Points example: 27. The original starter code returned 28 because round(25.99) rounded the base value up to 26.

## 2. Partial-refund example
Continuing with the previous purchase (transaction T1), where 27 points were originally awarded, I tested a partial refund of 100000 paise.

Refund validation: The total refunded amount is 100000 paise, which is within the original purchase amount of 259900 paise, so the refund is accepted.

Points reversal: 27 * 100000 // 259900 = 10. This means 10 points need to be reversed.

Balance update: The balance decreases from 27 to 17 points.

After processing the refund, the transaction is updated as follows:

{'amount_paise': 259900, 'awarded_points': 27, 'reversed_points': 10, 'refunded_paise': 100000}

The corresponding ledger entry is:

{'event_id': 'R1', 'type': 'refund_processed', 'transaction_id': 'T1', 'points_delta': -10, 'balance_after': 17}

This confirms that partial refunds are handled correctly and the remaining points are maintained accurately.

## 3. Three edge cases
Cap of zero: I tested calculate_points(50000, 2, 50, 0). The expected result was 0, and the function returned 0 as expected. This was verified using test_bonus_and_cap_matrix[50000-2-50-0-0].

Over-refund after partial refunds: I tested a purchase of 100000 paise that earned 10 points, followed by two refunds of 25000 paise each. After these refunds, the balance was 5 points. A third refund of 50001 paise was rejected because it exceeded the remaining refundable amount. The balance stayed at 5, and the total refunded amount remained 50000 paise. Verified using test_multiple_partial_refunds_then_over_refund.

Exactly at the repeat threshold: I tested two identical transactions with a threshold of 2. No alert was generated because the count must be greater than the threshold. When I added a third matching transaction, one alert was generated as expected. Verified using test_repeat_alert_respects_threshold.

## 4. Assumptions and limitations
Rounding: The code uses floor division at each calculation step. For refunds, points are reversed based on the cumulative refunded amount, ensuring that a full refund reverses exactly the points originally awarded.

Invalid values: Inputs that are not valid integers, including booleans, floats and strings, are rejected. Negative amounts and rules also return 0 points. A None cap means there is no points limit, while a missing bonus is treated as 0%.

Missing fields: Events without an event_id or transaction_id are ignored and are not added to the processed event list.

Refunds: A refund must be a positive integer and must belong to an existing transaction. The total refunded amount cannot exceed the original purchase amount. If any of these conditions fail, the entire event is ignored. The account balance is also prevented from going below zero.

Repeat alerts: An alert is generated only when the number of matching transactions is greater than the given threshold. Thresholds below 1 are treated as 1. Rows with missing account IDs or dates, or invalid amounts, are skipped. Every alert includes review_only: True, meaning it is only a warning and does not block transactions.

Known limitation: Currently, ignored events are not returned to the caller with a specific rejection reason. Adding this would make debugging and tracking rejected events easier.