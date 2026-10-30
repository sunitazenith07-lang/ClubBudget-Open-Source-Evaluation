# TESTING.md — Required submission

## Test command and environment

- **Python version:** Python 3.14.4 (Windows)
- **Commands run:**
  - `python -m pytest -q`
  - `python -m main`
- **Actual test summary:**
  - Baseline: 67 failed, 147 passed (214 tests).
  - Final: 248 passed, 0 failed.
  - Latest reported test runtime: 0.27 seconds.
  - Demo output:
    - `Points example: 27`
    - `Repeat warnings: []`

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | `amount_paise = 19999`, `points_per_100_rupees = 1` | Floor division should award 1 point, not 2. | Returned 1 point. | `tests/test_contract.py::test_points_use_floor` |
| 2 | `calculate_points(50000, 1, cap_points=0)` | A zero-point cap should result in 0 points. | Returned 0 points. | `tests/test_contract.py::test_cap_zero_is_respected` |
| 3 | Replaying the same captured purchase event | The event should be processed only once, without duplicate points or ledger entries. | Balance and ledger remained unchanged after replay. | `tests/test_acceptance_matrix.py::test_purchase_event_replay_is_idempotent` |
| 4 | Refund amount is `True`, negative, or greater than the original purchase amount. | Invalid or excessive refunds should not change the account. | Refund was ignored; balance and transaction remained unchanged. | `tests/test_acceptance_matrix.py::test_invalid_or_excess_refund_does_not_change_account` |
| 5 | Three refunds of 30,000, 30,000 and 40,000 paise on a 100,000-paise purchase that awarded 10 points. | The refunds should reverse 3, 3 and 4 points respectively. | Balance decreased from 10 to 7, then 4, then 0. | `tests/test_fintech_edge_cases.py::test_multi_step_cumulative_partial_refunds` |
| 6 | A refund needs to reverse 10 points, but only 2 points remain in the account. | The balance must never become negative. The ledger should record the actual deduction. | Balance became 0 and the ledger recorded -2 points. | `tests/test_fintech_edge_cases.py::test_ledger_negative_balance_prevention` |
| 7 | Multiple purchases and refunds on one account. | The balance should match the sum of ledger point changes for the tested events. | The test reported a matching balance of 5 points. | `tests/test_fintech_edge_cases.py::test_ledger_consistency_invariant` |

## Regression tests added

The added tests cover these defects and behaviours:

1. **Points calculation:** Checks floor division, zero rates, negative values, promotional bonuses and caps.
2. **Invalid purchase amounts:** Checks zero, negative, float, boolean and invalid input types.
3. **Duplicate events:** Checks that replayed purchases and duplicate transaction IDs do not award points twice.
4. **Refund validation:** Checks invalid, excessive and duplicate refunds.
5. **Partial refunds:** Checks proportional reversal across multiple refund events.
6. **Refund rounding:** Checks how fractional point remainders are handled.
7. **Ledger consistency:** Checks that ledger changes match the account balance in the tested scenarios.
8. **Missing identifiers:** Checks that missing event or transaction IDs do not cause invalid state changes.
9. **CSV statement:** Checks the account statement export.
10. **Dataset integration:** Checks reward rules and repeat-pattern detection using the supplied records.
11. **Spent points during refunds:** Checks that a refund does not make the balance negative.

## Remaining failures or limitations

- **Remaining test failures:** None in the latest reported run (248 passed).
- **Known limitations:**
  - Repeat alerts use exact account, date and amount matching. They do not use a rolling time window.
  - If points have already been spent outside this service, a refund can require reversing more points than are available. The balance is protected from becoming negative, but the remaining amount is not recovered automatically.
  - Repeat alerts are warnings for human review. They do not block transactions.