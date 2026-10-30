# REWARD_RULE_NOTES.md — Required submission

Complete this file with your own actual examples and results. Do not leave prompts unanswered.

## 1. Worked points calculation

**Scenario:** A customer makes a purchase of ₹2,599.00 (259,900 paise) with reward rules: `points_per_100_rupees = 1`, `bonus_percent = 10`, `cap_points = 100`.

**Step-by-step calculation:**

1. **Base points** — Count complete ₹100 blocks using floor division:
   - `base = floor(259900 / 10000) * 1`
   - `base = 25 * 1 = 25`
   - Rounding rule: Floor division (`//`) discards the remainder. 259,900 paise = ₹2,599.00, which contains 25 complete ₹100 blocks (the leftover ₹99.00 does not count).

2. **Apply bonus** — Add the bonus percentage using integer arithmetic:
   - `points = floor(25 * (100 + 10) / 100)`
   - `points = floor(25 * 110 / 100)`
   - `points = 2750 // 100 = 27`
   - Rounding rule: The multiplication is done first (`25 * 110 = 2750`), then integer floor division by 100 gives `27`. The fractional part is discarded.

3. **Apply cap** — Compare with the maximum allowed points:
   - `cap_points = 100`
   - `points = min(27, 100) = 27`
   - The cap is 100 and the calculated points are 27, so the cap does not reduce the result.

4. **Final clamp** — Ensure points are not negative:
   - `points = max(0, 27) = 27`

**Final result: 27 points.** Verified by running `python3 -m main`, which outputs `Points example: 27`.

## 2. Partial-refund example

**Scenario:** A customer purchases ₹1,000.00 (100,000 paise), earns 10 points, then returns ₹500.00 (50,000 paise) of the purchase.

**Step-by-step:**

1. **Original purchase** (event_id `"E1"`, transaction `"T1"`):
   - `base = 100000 // 10000 * 1 = 10`
   - `points = 10 * 100 // 100 = 10` (no bonus)
   - Balance becomes `10`. Ledger entry: `{event_id: "E1", type: "purchase_captured", points_delta: 10}`.
   - Transaction record: `{amount_paise: 100000, awarded_points: 10, reversed_points: 0, refunded_paise: 0}`.

2. **Partial refund** (event_id `"E2"`, amount 50,000 paise):
   - First, validate the refund: `50000` is a positive integer and `50000 + 0 <= 100000` (within bounds). Valid.
   - Update refunded amount: `refunded_paise = 0 + 50000 = 50000`.
   - Calculate proportional reversal: `should_reverse = 10 * 50000 // 100000 = 500000 // 100000 = 5`.
   - Calculate delta: `delta = 5 - 0 = 5` (5 points not yet reversed).
   - Deduct from balance: `balance = 10 - 5 = 5`.
   - Update transaction: `reversed_points = 5`, `refunded_paise = 50000`.
   - Ledger entry: `{event_id: "E2", type: "refund_processed", points_delta: -5}`.

**Final result: Balance = 5 points.** The customer kept 5 points for the ₹500 portion they did not return.

Verified by test `test_partial_refund_reverses_proportionally` and `test_purchase_then_refund_with_valid_event_ids`, both passing.

## 3. Three edge cases

### Edge case 1: Amount just below the ₹100 boundary

- **Input:** `calculate_points(9999, 1)` — 9,999 paise = ₹99.99.
- **Expected behaviour:** 0 points. The customer has not reached a complete ₹100 block.
- **Actual result:** 0 points. `9999 // 10000 = 0`.
- **Test:** `test_integer_floor_points_calculation[9999-0_0]` — passes.
- **Why this matters:** The original code used `round(9999/10000) = round(0.9999) = 1`, which incorrectly awarded 1 point. Floor division correctly returns 0.

### Edge case 2: Cap set to zero

- **Input:** `calculate_points(50000, 1, cap_points=0)` — ₹500 purchase, cap is zero.
- **Expected behaviour:** 0 points. The spec says "A cap of zero means zero points."
- **Actual result:** 0 points. `min(5, 0) = 0`.
- **Test:** `test_cap_zero_is_respected` — passes.
- **Why this matters:** The original code used `if cap_points:` which treated `0` as `False` (falsy in Python). The cap was skipped entirely, and the customer received 5 points instead of 0. The fix uses `if cap_points is not None:` which correctly distinguishes `0` (a valid cap) from `None` (no cap).

### Edge case 3: Refund with a boolean value (`True`) as the amount

- **Input:** Refund event with `amount_paise = True` on a 100,000 paise purchase.
- **Expected behaviour:** Account unchanged. A boolean is not a valid monetary amount.
- **Actual result:** Account unchanged. The refund is rejected by `isinstance(refund, bool)`.
- **Test:** `test_invalid_or_excess_refund_does_not_change_account[True]` — passes.
- **Why this matters:** In Python, `bool` is a subclass of `int`, so `isinstance(True, int)` returns `True`. Without the explicit `isinstance(refund, bool)` check, `True` would be treated as `1` paise and processed as a valid (but incorrect) refund. The fix uses a two-part check: first verify it is an `int`, then exclude `bool`.

## 4. Assumptions and limitations

**Rounding assumptions:**
- All monetary amounts are in integer paise (100 paise = ₹1). This avoids floating-point precision issues.
- Points calculation uses floor division (`//`) at every step, as specified. Partial ₹100 blocks are discarded, and fractional bonus points are rounded down.
- The `max(0, points)` at the end of `calculate_points` ensures points can never be negative, even if rules contain negative values for `bonus_percent` or `cap_points`.

**Missing-field handling:**
- Events with `event_id = None` (or a completely missing `event_id` key) are rejected immediately. This prevents the `None` collision bug and ensures every processed event can be tracked for dedup.
- Missing `amount_paise` defaults to `0` via `event.get('amount_paise', 0)`. A purchase with 0 paise earns 0 points.

**Repeat-alert threshold assumptions:**
- `flag_repeat_transactions` groups by `(account_id, date, amount_paise)` and flags groups where the count is **strictly greater than** the threshold (`len(ids) > threshold`).
- The default threshold is `2`, meaning 3 or more same-account, same-date, same-amount transactions trigger an alert.
- Alerts are advisory only. They never block transactions or modify balances.

**Unresolved issues:**
- The `processed_event_ids` list uses O(n) linear search. For accounts with very large event histories, a set would be more efficient, but this would require changing the data model.
- Negative `bonus_percent` and negative `cap_points` are not explicitly rejected. They produce results clamped to 0 by `max(0, ...)`, which is safe but could be validated earlier for clearer error reporting.
