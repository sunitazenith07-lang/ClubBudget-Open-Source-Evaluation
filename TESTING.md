# TESTING.md — Required submission

Complete this file with test evidence from your own work. Include at least five edge cases. Do not claim a test passed unless you ran it.

## Test command and environment
- Python version: `Python 3.x (WSL/Linux environment)`
- Command run: `python3 -m pytest -q`
- Actual test summary: `214 passed in 0.48s`

## Edge-case evidence

| # | Case / input | Expected behaviour | Actual result | Test name or evidence |
|---|---|---|---|---|
| 1 | `cap_points=0` | Promo cap of zero is strictly respected, returning 0 points | Passed with 0 points awarded | `test_cap_zero_is_respected` |
| 2 | Duplicate `event_id` replay | Event processed once; replaying does not duplicate points or ledger entries | Idempotency guard preserves account state unchanged | `test_idempotent_event_processing` |
| 3 | Malformed refund input (`None`, strings, lists) | Handled safely without raising unhandled runtime exceptions (`TypeError`) | Gracefully bypassed/ignored invalid input | `test_refund_type_safety_edge_cases` |
| 4 | Excess refund amounts exceeding original purchase | Refund is restricted or ignored to prevent negative state corruption | Refund capped to remaining allowable amount | `test_refund_exceeding_purchase_bounds` |
| 5 | Fractional paise amounts (`19999` paise) | Strict integer floor division truncation downwards (`// 10000`) | Floored correctly to 1 point baseline | `test_points_use_floor_division` |

## Regression tests added
List the defects fixed and the tests added to prevent them from returning.
- Defect 1: Rounding half-to-even via `round()` instead of integer floor division (`//`). Protected by standard acceptance matrix tests.
- Defect 2: Falsy evaluation of `cap_points=0`. Protected by zero-cap tests.
- Defect 3: Missing idempotency checks allowing duplicate transaction processing. Protected by event replay contract tests.
- Defect 4: `TypeError` crashes during malformed refund inputs. Protected by defensive type-checking and bounding guards.

## Remaining failures or limitations
List any known failing tests or unresolved behaviours honestly.
- None; all 214 tests in the evaluation suite pass successfully.