# TESTING.md — RewardBook Test Evidence

## Test command and environment

- **Python version:** Python 3.14.4
- **Command run:** `python -m pytest -q`
- **Baseline result:** 147 passed, 67 failed.
- **Current result:** 214 passed.
- **Test framework:** pytest

The baseline failures exposed issues in integer floor-based reward calculation, bonus and cap handling, duplicate event processing, and refund validation. After the implementation changes, the full test suite passed.

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|--------------|--------------------|---------------|-----------------------|
| 1 | Purchase amount of 19,999 paise | Award 1 point at 1 point per ₹100 | Passed | `test_integer_floor_points_calculation` |
| 2 | Reward cap set to zero | Award zero points | Passed | `test_cap_zero_is_respected`, `test_bonus_and_cap_matrix` |
| 3 | Same purchase event replayed | Balance and ledger must not be updated twice | Passed | `test_purchase_event_replay_is_idempotent`, `test_purchase_event_once` |
| 4 | Refund greater than original purchase amount | Reject refund without changing balance or refunded amount | Passed | `test_refund_amount_bounds_and_balance`, `test_invalid_or_excess_refund_ignored` |
| 5 | Partial refund of 50,000 paise on a 100,000-paise purchase | Reverse 50% of the awarded points | Passed | `test_partial_refund_reverses_proportionally` |
| 6 | Declined purchase event | Do not award reward points | Passed | `test_unrecognized_or_declined_events_do_not_award_points`, `test_declined_event_does_not_award` |
| 7 | Same transaction pattern across different accounts | Do not group unrelated accounts together | Passed | `test_repeat_alerts_do_not_mix_distinct_keys`, `test_different_accounts_not_grouped` |

## Regression tests

The existing contract and acceptance test suites cover the following defects and behaviours:

- Integer floor-based reward calculation instead of rounding.
- Correct application of bonus percentages and reward caps, including a zero cap.
- Idempotent processing of repeated event IDs.
- Consistent purchase transaction and reward-point records.
- Rejection of negative, zero, malformed and excessive refund amounts.
- Proportional reversal of points for partial refunds.
- Safe handling of unknown and declined events.
- Repeat-transaction grouping by account, date and amount.
- Repeat-alert threshold boundaries.
- Input account immutability.

The regression coverage is provided by `tests/test_contract.py` and `tests/test_acceptance_matrix.py`.

## Remaining failures or limitations

- Missing or empty event and transaction identifiers have not been independently verified.
- Malformed purchase amounts and malformed reward-rule types require additional validation.
- The repeat-alert function uses a strict greater-than threshold (`count > threshold`).
- Repeat alerts identify possible patterns for human review; they do not establish fraud or block transactions.
- The current test suite does not establish production database persistence or concurrent event-processing safety.

No current test failures were reported in the verified full-suite run.