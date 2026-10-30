# Approach and implementation decisions

## 1. Baseline

- Commands run before implementation:
  - `python -m pip install -r requirements-dev.txt`
  - `python -m pytest -q`
  - `python -m main`
- Initial test result: `214 tests; 147 passed, 67 failed, 0 skipped`.
- The baseline demo output was:

  ```text
  Points example: 28
  Repeat warnings: []
  ```

The baseline failures showed that the starter implementation was incomplete in point-boundary handling, cap handling, purchase replay handling, and refund validation.

## 2. Codebase understanding

The main business logic is in `service.py`. `models.new_account()` creates an account dictionary with `points_balance`, `processed_event_ids`, `transactions`, and `ledger`. `fixtures.py` supplies the demo rules and repeat-transaction rows, and `main.py` calls `calculate_points()` and `flag_repeat_transactions()`.

The event flow is:

1. A captured purchase is passed to `apply_reward_event()` with an account and rules.
2. `calculate_points()` computes the awarded points.
3. The transaction record, account balance, processed-event list, and purchase ledger are updated.
4. A later refund uses the stored transaction amount, awarded points, cumulative refund amount, and previous reversal.
5. `flag_repeat_transactions()` groups rows by account, date, and amount and returns advisory groups.

The account is deep-copied before event processing, so calls return updated account data without mutating the input account.

## 3. Investigation and implementation strategy

### Issue 1: Point calculation used rounding

The starter used `round(amount_paise / 10000)`, which awarded points above the required floor boundary. The baseline tests included failures such as amounts just below a ₹100 boundary receiving an extra point.

The calculation was changed to integer floor division:

```text
base_points = (amount_paise // 10000) * points_per_100_rupees
bonus_points = (base_points * (100 + bonus_percent)) // 100
```

The cap is applied after the bonus. Inputs are validated as non-negative integers, boolean numeric values are rejected, and `cap_points=0` is treated as an active cap.

### Issue 2: Purchase events were not fully idempotent

The starter prevented a second award when a transaction ID already existed, but it appended the same event ID again. The replay tests therefore failed because processed IDs and event state changed on replay.

The implementation now validates non-empty string event and transaction identifiers, checks `processed_event_ids` before financial processing, and returns the copied account unchanged for a replay. Existing transaction IDs do not receive another award, overwrite, or purchase ledger entry.

### Issue 3: Refund validation and proportional reversal were incomplete

The starter accepted negative and excessive refunds and could raise errors for malformed refund amounts. It also mutated transaction state before validating the refund.

The refund path now validates the refund amount, transaction ID, stored transaction fields, refund limit, and resulting balance before mutation. Refunds use cumulative integer arithmetic:

```text
cumulative_refund = previous_refunded_paise + accepted_refund_paise
total_reversal = (awarded_points * cumulative_refund) // original_amount_paise
incremental_reversal = total_reversal - previous_reversed_points
```

This prevents reversal beyond awarded points and prevents an accepted refund from making the balance negative. The ledger delta is calculated from the actual balance before and after the accepted transition.

### Issue 4: Missing purchase amounts were accepted as zero

The final audit found that `event.get('amount_paise', 0)` treated a missing captured-purchase amount as an explicit zero. That could create a zero-point transaction and financial ledger entry. The lookup now has no zero default, so missing, `None`, and other malformed amounts fail the existing integer/non-negative validation before financial mutation. Explicit zero remains accepted.

## 4. Implementation decisions

- Integer arithmetic was selected because the requirements define floor behavior and paise are integral units.
- Cumulative refund calculation was selected so repeated partial refunds are floored once at the cumulative total rather than independently.
- Validation occurs before financial mutation so rejected refunds cannot change transaction totals, reversal totals, balances, or financial ledger entries.
- A valid event ID for a rejected event is recorded as processed according to the implementation, but rejected events do not create financial ledger entries.
- Missing event IDs are rejected without processing. Missing purchase or refund transaction IDs are rejected without financial mutation.
- Unknown refunds are rejected without creating a transaction or financial ledger entry.
- Existing inconsistent transaction or balance state is not silently repaired; an invalid refund transition is rejected.
- Captured purchases require an explicit non-negative integer amount. Zero is valid and produces a zero-value transaction with a zero-impact ledger entry.

## 5. Verification

Seven refund regression tests were added to `tests/test_contract.py`:

- `test_multiple_partial_refunds_use_incremental_cumulative_reversals`
- `test_partial_refund_rounding_is_cumulative_and_bounded`
- `test_refund_replay_does_not_change_account_or_ledger`
- `test_each_accepted_refund_has_consistent_single_ledger_entry`
- `test_refund_order_preserves_cumulative_total_reversal`
- `test_multiple_refunds_do_not_mutate_input_account`
- `test_excessive_refund_leaves_financial_state_and_ledger_unchanged`

Four final purchase-validation regression tests were then added:

- `test_purchase_missing_amount_is_rejected_without_financial_mutation`
- `test_purchase_none_amount_is_rejected_without_financial_mutation`
- `test_purchase_non_integer_amount_is_rejected_without_financial_mutation`
- `test_purchase_zero_amount_remains_accepted`

An earlier implementation milestone was reported as `221 passed` before the final purchase-validation tests were added. The final reported result was:

```text
225 passed in 2.12s
```

The previously reported final demo output was:

```text
Points example: 27
Repeat warnings: []
```

The visible tests do not exhaustively cover malformed account containers or every possible inconsistent historical account state. The larger `data/records.json` dataset is not loaded by `python -m main`.
