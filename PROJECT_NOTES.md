# Project Notes — RewardBook

## Requirements completed
1. **Integer Floor Arithmetic Points Engine:**
   - Implemented `floor(amount_paise / 10000) * points_per_100_rupees`.
   - Implemented `floor(base_points * (100 + bonus_percent) / 100)`.
   - Clamped to optional `cap_points` (explicitly handling `cap_points = 0` and negative caps).
   - Validated invalid/negative amounts and rules to return 0 points.
2. **Event Filtering and Idempotency:**
   - Handled `purchase_captured` events exclusively for points awarding.
   - Enforced strict idempotency using `account['processed_event_ids']` so replays cannot duplicate balance additions or ledger entries.
   - Guarded against declined (`purchase_declined`), pending, and unknown event types.
3. **Proportional Refund Reversal:**
   - Validated refund amounts against original transaction amounts and remaining refundable paise.
   - Implemented cumulative integer proportional calculation eliminating rounding drift on multi-step partial refunds.
   - Prevented negative balance overdrafts by clamping delta to available `points_balance`.
4. **Audit Ledger Integrity:**
   - Appended auditable ledger records (`{'event_id', 'type', 'points_delta'}`) for all accepted capture and refund events.
5. **Repeat Transaction Alerts:**
   - Grouped transactions by `(account_id, date, amount_paise)` and flagged groups exceeding `threshold`.
   - Provided deterministic ordering and robust handling of missing/malformed records.
6. **Optional Stretch Work:**
   - Implemented `generate_account_statement_csv(account)` to output CSV format ledger statements.

## Files changed
- `service.py`: Fixed calculation, event processing, refund reversal, repeat alerts, and added CSV statement generation.
- `tests/test_regression_and_edge_cases.py`: Created test suite with 9 comprehensive regression and edge case tests.
- `approach.md`: Completed 5-mark documentation.
- `challenges.md`: Completed compulsory 5-mark documentation.
- `optimizations.md`: Completed 5-mark documentation.
- `TESTING.md`: Completed testing records and 7 documented edge cases.
- `REWARD_RULE_NOTES.md`: Completed worked calculation, refund example, edge cases, and assumptions.

## Decisions and assumptions
- All financial calculations rely on integer floor arithmetic (`//`) to eliminate IEEE 754 precision errors.
- Python booleans (`True`, `False`) are explicitly disqualified from numeric validity checks despite `isinstance(True, int) == True`.
- Account objects passed to `apply_reward_event` are deep-copied to guarantee caller immutability.
- Repeat alerts serve as non-blocking operational flags for human review.

## Tests and results
- Initial baseline: 67 failed, 147 passed (out of 214 tests).
- Final test suite: 223 passed, 0 failed in 0.20s (100% pass rate).
- Demo execution (`python -m main`): Points example: 27, Repeat warnings: [].

## Limitations and next steps
- When an account balance is lower than the computed refund delta (e.g. points were already transferred or redeemed), the reversal is clamped at zero. An unrecovered balance liability mechanism could be added for long-term ledger reconciliation.

