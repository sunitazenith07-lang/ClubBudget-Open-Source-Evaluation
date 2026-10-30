# challenges.md - COMPULSORY submission

This file is mandatory and worth 5 marks. Describe your actual experience honestly. Do not invent difficulties to fill the page.

## 1. Challenge or confusing behaviour

The hardest challenge was understanding why `test_invalid_or_excess_refund_does_not_change_account` tested the refund amount `True` (a Python boolean) alongside numeric values like `-1`, `150000`, `None`, `"100"`, `1.5`, `[]`, and `{}`.

The test expected that passing `True` as the refund `amount_paise` should leave the account unchanged — meaning `True` is invalid. But in Python, `isinstance(True, int)` returns `True` because `bool` is a subclass of `int`. So a simple `isinstance(refund, int)` check would accidentally accept `True` as a valid amount.

A second challenge was the `None` event_id collision. After implementing the event-ID idempotency guard (`if event_id in processed_event_ids`), I discovered a new problem: if two unrelated events both had a missing `event_id`, both resolved to `None` via `dict.get()`. The first `None` was added to `processed_event_ids`, and the second legitimate event was silently blocked because `None in [None]` is `True`. This was a bug introduced by the fix itself.

## 2. Evidence

**Boolean challenge evidence:**

The test at `tests/test_acceptance_matrix.py` line 79 parameterizes the refund amount with `True`:

```
@pytest.mark.parametrize("amount", [0,-1,-50,-1000,100001,150000,200000,999999,True,None,"100",1.5,[],{},False])
def test_invalid_or_excess_refund_does_not_change_account(amount):
```

When I first added only `if not isinstance(refund, int)`, the test for `True` still failed because `isinstance(True, int)` is `True` in Python. Similarly, `isinstance(False, int)` is also `True`.

**None collision evidence:**

After adding `if event_id in out['processed_event_ids']: return out` but before adding the `None` guard, I tested this scenario manually:

```python
a = new_account("A")
e1 = {"type": "purchase_captured", "transaction_id": "T1", "amount_paise": 50000}
e2 = {"type": "purchase_captured", "transaction_id": "T2", "amount_paise": 80000}
a = apply_reward_event(a, e1, rules)  # processed_event_ids becomes [None]
a = apply_reward_event(a, e2, rules)  # None in [None] → True → rejected!
```

Result: `a["points_balance"]` was `5` instead of the expected `13` (5 + 8). Transaction T2 was never recorded.

## 3. What I tried

**For the boolean challenge:**

1. First attempt: `if not isinstance(refund, int)` — This rejected `None`, `"100"`, `1.5`, `[]`, `{}`, but still accepted `True` and `False` because `bool` inherits from `int`.
2. Checked Python docs: confirmed that `bool` is a subclass of `int` (`True == 1`, `False == 0`).
3. Second attempt: Added `isinstance(refund, bool)` as a separate exclusion. The combined check `if not isinstance(refund, int) or isinstance(refund, bool)` correctly rejects booleans while accepting real integers.
4. Verified that `refund <= 0` also catches `False` (since `False == 0` and `0 <= 0` is True), but `True` would slip through (`True == 1`, `1 <= 0` is False). So the explicit `isinstance(refund, bool)` check is necessary.

**For the None collision:**

1. Traced the problem: `event.get('event_id')` returns `None` when the key is missing. This `None` was being appended to `processed_event_ids`.
2. Tested adding `if event_id is None: return out` before the idempotency check.
3. Verified that both events with missing IDs are now safely rejected without polluting `processed_event_ids`, and that legitimate events with valid IDs still work normally.

## 4. Resolution

**Boolean:** The root cause is Python's type hierarchy where `bool` is a subclass of `int`. The fix at `service.py` line 33 is:

```python
if not isinstance(refund, int) or isinstance(refund, bool) or refund <= 0:
    return out
```

This checks three conditions:
1. Is it not an integer at all? (catches `None`, `str`, `float`, `list`, `dict`)
2. Is it a boolean? (catches `True` and `False` specifically)
3. Is it zero or negative? (catches `0` and negative numbers)

If any condition is true, the refund is rejected and the account is returned unchanged.

**None collision:** The root cause is that `dict.get()` returns `None` for missing keys, and `None` is a valid value for the `in` operator on lists. The fix at `service.py` lines 17–19 rejects events with `None` event_id before any processing:

```python
if event_id is None:
    return out
```

This prevents `None` from entering `processed_event_ids` and colliding with future events.

## 5. Proof and regression prevention

**Boolean fix proven by:**
- `test_invalid_or_excess_refund_does_not_change_account[True]` — now passes (was failing).
- `test_invalid_or_excess_refund_does_not_change_account[False]` (parameterized as `amount13`) — now passes.

**None collision fix proven by:**
- `test_two_different_purchases_with_none_event_id_both_rejected` in `tests/test_event_id_regression.py` — verifies that two events both missing `event_id` are both rejected without collision.
- `test_none_event_id_purchase_is_rejected` — verifies a single `None` event_id purchase is rejected.
- `test_missing_event_id_key_purchase_is_rejected` — verifies a completely missing `event_id` key is rejected.
- `test_none_event_id_refund_is_rejected` — verifies `None` event_id refunds are rejected.

**What could still break:**
- If a future change removes the `deepcopy` at line 15 of `service.py`, the input account could be mutated. The test `test_input_account_not_mutated_by_none_event_id` would catch this.
- If `processed_event_ids` were changed from a list to a set, the `in` operator would still work, so the idempotency logic would be preserved.

## 6. Unresolved challenge or next step

The `processed_event_ids` list uses O(n) linear search for the `in` operator. For accounts with thousands of events, this becomes slow. Measured performance: ~0.01 ms per call at 100 events, ~3.2 ms at 50,000 events. This is acceptable for the current synthetic dataset (max ~7 events per account) but would need optimization for production scale.

If I had more time, I would consider changing `processed_event_ids` to a set for O(1) lookups. This would require updating `models.py` and verifying that JSON serialization (which does not natively support sets) still works, possibly by converting to/from a list during serialization.

If you did not encounter a major blocker, say so honestly and document the hardest edge case you deliberately tested and what it taught you. Do not manufacture a story.
