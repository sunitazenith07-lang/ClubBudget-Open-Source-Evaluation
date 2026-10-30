# RewardBook — Reward Rule Notes

## 1. Points calculation

Amounts are stored in paise. One hundred rupees is `10,000` paise, so base points use integer floor division:

```text
base_points = (amount_paise // 10000) * points_per_100_rupees
```

The bonus is then applied with integer floor division. The optional cap is applied last. Invalid or negative amounts and rule values return zero points, and boolean values are rejected as numeric inputs. A cap of zero is active and produces zero points.

Worked example:

```text
Purchase amount: 50,000 paise
Points per ₹100: 2
Bonus: 50%
Cap: 6

Base points = (50,000 // 10,000) * 2 = 10
After bonus = (10 * 150) // 100 = 15
After cap = min(15, 6) = 6 points
```

## 2. Partial refund example

Assume a captured purchase of `100,000` paise awarded `10` points. Refunds use the cumulative refunded amount and integer floor division:

```text
total_reversal = (awarded_points * cumulative_refund) // original_amount
incremental_reversal = total_reversal - previous_reversed_points
```

| Refund | Cumulative refund | Cumulative reversal | Incremental reversal | Balance attributable to purchase |
|---:|---:|---:|---:|---:|
| 25,000 paise | 25,000 paise | 2 points | 2 points | 8 points |
| 25,000 paise | 50,000 paise | 5 points | 3 points | 5 points |
| 50,000 paise | 100,000 paise | 10 points | 5 points | 0 points |

The final balance attributable to this purchase is zero. Cumulative integer arithmetic avoids rounding each partial refund independently and then accumulating inconsistent totals. The regression test `test_multiple_partial_refunds_use_incremental_cumulative_reversals` verifies the `2`, `3`, and `5` incremental reversals.

## 3. Ledger behavior

Each accepted captured purchase creates one transaction and one ledger entry. Each accepted refund creates one ledger entry. Replayed events return without adding another financial ledger entry.

The ledger preserves the existing structure:

```text
{
    "event_id": event_id,
    "type": event_type,
    "points_delta": actual_balance_after - actual_balance_before
}
```

Purchase entries have a positive or zero delta. Accepted refund entries have the negative incremental reversal as their delta. The test `test_each_accepted_refund_has_consistent_single_ledger_entry` verifies that each accepted refund adds exactly one entry and that its `points_delta` matches the balance change.

## 4. Edge cases

1. **Amount below 10,000 paise**

   An amount such as `9,999` paise earns zero base points because floor division produces zero. This is covered by `test_integer_floor_points_calculation` in `tests/test_acceptance_matrix.py`.

2. **Zero reward cap**

   `cap_points=0` is applied rather than treated as absent, so the result is zero points. This is covered by `test_cap_zero_is_respected` and the zero-cap case in `test_bonus_and_cap_matrix`.

3. **Invalid or negative inputs**

   Negative amounts and invalid or negative rule values do not generate points. Boolean numeric inputs are rejected by the implementation. This is covered by `test_negative_amount_gives_zero`, `test_invalid_purchase_amount_awards_zero_points`, and `test_invalid_rule_values_do_not_create_negative_points`.

4. **Duplicate purchase event**

   Replaying a captured purchase event with the same event ID does not award points again, overwrite the transaction, or add another purchase ledger entry. This is covered by `test_purchase_event_once` and `test_purchase_event_replay_is_idempotent`.

5. **Duplicate refund event**

   Replaying the same valid refund event returns the account unchanged, so the balance, transaction data, ledger, and processed-event state do not change a second time. This is covered by `test_refund_replay_does_not_change_account`.

6. **Excessive refund**

   A refund greater than the remaining refundable amount is rejected without changing the balance, transaction refund totals, reversed points, or financial ledger. This is covered by `test_excessive_refund_leaves_financial_state_and_ledger_unchanged` and `test_refund_amount_bounds_and_balance`.

7. **Unknown refund transaction**

   A refund for an unknown transaction does not change the balance or create a transaction. This is covered by `test_unknown_refund_safe`.

8. **Pending or declined purchase**

   Only `purchase_captured` events award points. Pending, declined, and other unsupported event types do not award points or create purchase transactions. This is covered by `test_declined_event_does_not_award` and `test_unrecognized_or_declined_events_do_not_award_points`.

9. **Missing or malformed purchase amount**

   A captured purchase must explicitly provide a non-negative integer `amount_paise`. Missing, `None`, string, float, boolean, list, dictionary, and negative values are rejected without changing balance, transactions, or the financial ledger. A valid event ID is still recorded as processed. This is covered by `test_purchase_missing_amount_is_rejected_without_financial_mutation`, `test_purchase_none_amount_is_rejected_without_financial_mutation`, and `test_purchase_non_integer_amount_is_rejected_without_financial_mutation`.

10. **Zero-amount purchase**

   An explicit `amount_paise=0` remains valid under the existing contract. It creates a zero-value transaction and one zero-impact ledger entry while leaving the points balance unchanged. This is covered by `test_purchase_zero_amount_remains_accepted`.

## 5. Implementation decisions and assumptions

- **Event ID idempotency:** A valid, non-empty string `event_id` is checked against `processed_event_ids` before financial processing. A replay returns the deep-copied account without further changes.
- **Missing identifiers:** A missing or empty `event_id` is rejected without processing. A purchase or refund with a missing or empty `transaction_id` is rejected without financial mutation. `None` is not used as an identifier.
- **Rejected valid event IDs:** When an event has a valid ID but is rejected because its purchase/refund data is invalid, its ID is recorded in `processed_event_ids`. Rejected events do not create financial ledger entries.
- **Purchase amount validation:** Captured purchases require an explicit non-negative integer amount. Zero is accepted; missing and malformed amounts are rejected.
- **Cumulative refund rounding:** Refund totals are accumulated in paise. Total reversal is floored from the cumulative refund, and only the difference from the previous reversal is applied.
- **Invalid existing transaction state:** Refund processing validates the original amount, awarded points, previous refund amount, previous reversal, and account balance. If the stored transaction or balance is invalid, the refund is rejected rather than silently repairing historical state.
- **Repeat alerts:** `flag_repeat_transactions` groups possible repeats by account, date, and amount. Alerts are advisory output for human review and do not block transactions or automatically accuse a customer.

## 6. Limitations

- `data/records.json` is not loaded by `python -m main`. The demo uses the sample rules and transactions from `fixtures.py`; the JSON dataset is additional investigation and test material.
- The visible tests do not exhaustively cover every malformed account container or every possible inconsistent historical account state.
- The demo prints repeat warnings but does not provide a separate workflow for reviewing or resolving them.
