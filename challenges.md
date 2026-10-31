# Debugging notes

> **AI-use disclosure:** AI assistance was used with evaluator permission, as confirmed by the requester. See [AI_USAGE.md](AI_USAGE.md) for details.

## 1. Issue investigated

The tricky behavior was applying multiple partial refunds without reversing too many points or allowing the same refund event to apply more than once.

## 2. Evidence

The baseline had **67 failed and 147 passed**. Failing cases included `test_invalid_or_excess_refund_ignored` and parametrized refund bounds in `test_acceptance_matrix.py`. The synthetic dataset also includes missing event IDs and refund amounts with types such as float, list, bool, string, and dict.

## 3. Investigation performed

- Read the refund calculation and compared it with the acceptance tests and the written problem contract.
- Ran the baseline suite and demo from the project directory.
- Checked the shape and malformed-value types in `data/records.json`.
- Added regression cases for duplicate refund replay, cumulative partial refunds, invalid values, and missing IDs.

## 4. Root cause and resolution

The original refund path added the refund amount without checking the remaining refundable amount, and it did not use processed IDs to block replay. Validation now rejects invalid or excessive refunds, event IDs are checked before processing, and point reversals are calculated proportionally using integer arithmetic, bounded by the awarded points and current balance.

## 5. Proof and regression prevention

The final suite passed **221 tests**. In particular:

- `test_refund_event_replay_is_idempotent` checks that replay leaves balance, refund total, event IDs, and ledger length unchanged.
- `test_cumulative_refunds_cannot_exceed_purchase_amount` checks a rejected over-refund followed by a valid remaining refund.
- `test_zero_repeat_threshold_flags_a_single_valid_transaction` checks that validation did not accidentally change threshold-zero behavior.

## 6. Limitations

The function accepts dictionaries under its declared interface; arbitrary malformed account structures are not comprehensively normalized. Event IDs are marked processed before the event's type and payload are validated, so a later corrected payload using the same ID will be treated as a replay. Any change to that policy should be agreed with the event-delivery contract and covered by tests.

No pull request or evaluator review has been completed.
