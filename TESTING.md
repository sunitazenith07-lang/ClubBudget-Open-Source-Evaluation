# TESTING.md — Required submission

# Test command and environment
- Python version: 3.13.15 (via `python` at C:\Users\yashk\OneDrive\Desktop\python.exe) and 3.14.7 (via `py` launcher)
- Command run: `python -m pytest -q`
- Actual test summary: **214 passed, 0 failed** in 0.45s

# Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | `amount_paise=19999, rate=1` | 1 point (floor division, not rounding) | 1 point | `test_points_use_floor`, `test_integer_floor_points_calculation[19999,1]` |
| 2 | `cap_points=0` | 0 points despite earnings | 0 points | `test_cap_zero_is_respected`, `test_bonus_and_cap_matrix[50000,2,50,0,0]` |
| 3 | Replay same `event_id` ("E1") twice | `processed_event_ids == ['E1']`, balance not doubled | `['E1']`, balance unchanged | `test_purchase_event_once`, `test_purchase_event_replay_is_idempotent[PURCHASE-000]` |
| 4 | Refund `amount_paise=None` | TypeError avoided; account unchanged, `refunded_paise==0` | Account unchanged | `test_invalid_or_excess_refund_does_not_change_account[None]` |
| 5 | Refund `amount_paise=True` (bool) | Rejected (bool is not a valid int refund) | Account unchanged | `test_invalid_or_excess_refund_does_not_change_account[True]` |
| 6 | Refund `amount_paise=150000` on purchase of 100000 | Excess rejected; `refunded_paise==0`, balance stays 10 | `refunded_paise==0`, balance 10 | `test_invalid_or_excess_refund_does_not_change_account[150000]` |
| 7 | `amount_paise=-10000` | 0 points for negative amount | 0 points | `test_negative_amount_gives_zero`, `test_invalid_purchase_amount_awards_zero_points[-1]` |
| 8 | `bonus_percent=50, cap_points=6` on 50000 paise | Base 10, bonus → 15, capped to 6 | 6 points | `test_bonus_and_cap_matrix[50000,2,50,6,6]`, `test_bonus_then_cap` |

# Regression tests added
No test files were added or modified. All existing tests in `tests/test_acceptance_matrix.py` and `tests/test_contract.py` were preserved unchanged. The defects fixed were:
- Rounding → floor division in `calculate_points`
- `cap_points=0` truthiness bug in `calculate_points`
- Missing idempotency guard in `apply_reward_event`
- Missing refund type/bounds validation in `apply_reward_event`

# Remaining failures or limitations
None. All 214 tests pass with 0 failures.