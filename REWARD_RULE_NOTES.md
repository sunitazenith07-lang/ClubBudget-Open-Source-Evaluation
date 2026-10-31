# Reward rule examples

> **AI-use disclosure:** AI assistance was used with evaluator permission, as confirmed by the requester. See [AI_USAGE.md](AI_USAGE.md) for details.

## 1. Worked points calculation

Use the demo rules with a purchase of 259,900 paise, 1 point per 100 rupees, a 10% bonus, and a 100-point cap.

- Eligible 100-rupee units: `259900 // 10000 = 25`.
- Base points: `25 * 1 = 25`.
- Bonus: floor `25 * (100 + 10) // 100 = 27`.
- Apply cap: `min(27, 100) = 27`.
- Observed demo output: `Points example: 27`.

All calculations use integer arithmetic; fractional points are floored.

## 2. Partial refund

Capture a 100,000-paise purchase at 1 point per 100 rupees:

- Awarded: `100000 // 10000 = 10` points.
- Refund: 50,000 paise, half the purchase.
- Cumulative reversal: `10 * 50000 // 100000 = 5` points.
- Resulting balance: `10 - 5 = 5` points.
- Refund ledger entry: `{"event_id":"R","type":"refund_processed","points_delta":-5}`.

This behavior is covered by `test_partial_refund_reverses_proportionally` in `tests/test_contract.py`; replay protection is additionally covered by `test_refund_event_replay_is_idempotent`.

## 3. Edge cases

1. **Below a points boundary:** 9,999 paise at rate 1 yields 0 points; verified by `test_integer_floor_points_calculation[9999-0]`.
2. **Zero cap:** 50,000 paise with a 2-point rate, 50% bonus, and zero cap yields 0 points; verified by the corresponding parameter in `test_bonus_and_cap_matrix`.
3. **Cumulative refunds:** a 60,000-paise refund followed by an excessive 50,000-paise refund on a 100,000-paise purchase leaves the refundable total at 60,000. Refunding the remaining 40,000 reverses all 10 awarded points; verified by `test_cumulative_refunds_cannot_exceed_purchase_amount`.

## 4. Assumptions and limitations

- Amounts are integer paise; booleans, floats, strings, containers, and negative values are invalid rather than coerced.
- The base-point and bonus calculations both floor using integer division; cap is applied last, and zero is a valid cap.
- Repeat alerts use `group_size > threshold`; threshold zero flags any valid transaction, while negative thresholds are rejected.
- A missing/blank event ID or transaction ID prevents applying a purchase/refund. Event IDs are recorded before event payload validation, so an invalid event cannot be retried under the same ID with a corrected payload.
- These examples are based on executed tests and demo output. The demo and test suite were re-run on 2026-10-31.
