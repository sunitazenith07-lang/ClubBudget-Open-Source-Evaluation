# Challenges and resolutions

## 1. Challenge or confusing behaviour

The hardest part was not one isolated error, but keeping several related reward rules consistent at their boundaries:

- Currency is provided in paise, but points are earned per complete 100-rupee unit. Using ordinary rounding would award points for an incomplete unit.
- Refunds can be partial, so the amount already refunded and points already reversed must be considered together.
- Both purchase and refund events can be replayed. A repeated event must not change the account a second time.
- Repeat alerts use a strict threshold: a group at the threshold is not an alert; only a group above it is.

The most important distinction I had to keep clear was between a transaction ID and an event ID. A transaction ID identifies the purchase being captured or refunded; an event ID identifies a particular incoming event and is used to prevent replay.

## 2. Evidence

The untouched implementation used `round(amount_paise / 10000)`. That produced incorrect results just below a 100-rupee boundary. The tests expect:

- `calculate_points(9999, 1) == 0`
- `calculate_points(19999, 1) == 1`

The starter also used a truthiness check for `cap_points`, which treated a cap of zero as if no cap had been supplied. The contract test `test_cap_zero_is_respected` expects zero points for a zero cap.

In event processing, the starter appended event IDs unconditionally and did not check whether a refund event had already been processed. The requirements call for idempotent purchase and refund processing. Invalid refund inputs also needed to leave the existing refund total and balance unchanged; the acceptance matrix covers zero, negative, excessive, boolean, missing, and non-integer values.

For repeat alerts, the acceptance tests check both threshold boundaries and distinct grouping keys. With a threshold of two, two matching rows should not produce an alert, while three should.

## 3. What I tried

1. I read the problem statement's required behaviours and the visible tests before changing the service. This identified integer floor rounding, bonus-before-cap ordering, event replay handling, refund bounds, and the strict repeat threshold as acceptance requirements.
2. I ran `python -m pytest -q` against the starter. It failed on the above behavior areas, which confirmed that the defects were observable in the test suite. I did not retain the exact baseline summary, so I am not reporting an exact failure count.
3. I compared the failing point examples with the specified formula. This showed that the problem was the rounding operation itself, not the test expectations.
4. I traced purchase and refund handling through `apply_reward_event`. This showed that replay protection needed to happen before any event-specific account mutation, and that refunds needed validation before increasing the cumulative refunded amount.
5. I checked the repeat-alert examples against the function's grouping key and threshold comparison. The intended behavior is to group on account, date, and amount and alert only when the count is greater than the threshold.
6. After the changes, I ran the full visible suite and the offline demo. The suite passed; the demo output helped confirm that the sample rules produced 27 points and that the sample group of two did not exceed the default alert threshold.

## 4. Resolution

- **Point boundaries:** Replaced floating-point rounding with integer floor division. Bonus points are calculated with integer arithmetic, and the cap is applied last. The cap check uses `is not None`, so a cap of zero is respected.
- **Event replay:** Require a non-empty event ID and check it against the account's processed IDs before applying event effects. Once accepted for processing, an event ID is recorded once. This covers both purchase and refund replays.
- **Refund validation:** Validate the refund type, positivity, transaction amount, and cumulative refund limit before changing the transaction. Calculate the cumulative proportional reversal with integer arithmetic, limit it to the originally awarded points, and prevent the resulting balance from becoming negative.
- **Repeat alerts:** Keep the grouping key as `(account_id, date, amount_paise)`, ignore rows with missing or malformed identifiers/amounts, and report only groups whose length exceeds the threshold.

These changes correct the underlying operations rather than adjusting expected test values or suppressing failures.

## 5. Proof and regression prevention

The final command `python -m pytest -q` completed with **217 passed in 0.32s** on Python 3.14.7. The offline demo `python -m main` also completed successfully and printed:

```text
Points example: 27
Repeat warnings: []
```

Regression cases include:

- `test_integer_floor_points_calculation` and `test_points_use_floor` for paise boundaries.
- `test_bonus_and_cap_matrix` and `test_cap_zero_is_respected` for bonus ordering and zero caps.
- `test_purchase_event_replay_is_idempotent` and `test_refund_event_replay_is_idempotent` for event replay.
- `test_partial_refund_reverses_proportionally` and `test_invalid_or_excess_refund_does_not_change_account` for refund behavior.
- `test_missing_event_identifier_cannot_award_purchase` for missing event IDs.
- `test_repeat_alert_threshold_boundaries` and `test_repeat_groups_ignore_records_missing_identifiers` for alert thresholds and malformed grouping data.

## 6. Unresolved challenge or next step

The service is an in-memory exercise, not a persistent or concurrency-safe ledger. The visible tests do not establish behavior when two workers process the same event simultaneously, when account history becomes very large, or when an account mapping itself has malformed nested fields.

If extending this beyond the exercise, I would first define the storage and concurrency contract, then enforce event-ID uniqueness in persistent storage and add tests for concurrent duplicate events and process restarts. I would also add explicit tests for multiple distinct partial refunds whose individual amounts cause integer-rounding boundaries, and verify that cumulative reversal totals never exceed awarded points. No performance benchmark was run, so I do not claim a measured speed or memory improvement.
