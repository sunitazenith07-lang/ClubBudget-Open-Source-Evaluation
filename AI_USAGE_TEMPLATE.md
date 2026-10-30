# AI-Use Declaration — RewardBook

## 1. Tool and Model Used
- **Tool / Assistant:** Antigravity IDE (Gemini 3.8 Flash)
- **Purpose:** Pair-programming assistant for tracing code/data flow, debugging runtime failure logs, running regression suites, and generating architecture documentation.

## 2. Independent Verification and Changes
- **Arithmetic Verification:** Traced points formula manually on paper and verified that integer floor division `// 10000` prevents fractional rounding errors caused by Python's `round()`.
- **Python Type Behavior Investigation:** Verified that `issubclass(bool, int)` is `True` in Python, confirming why `isinstance(True, int)` caused boolean values to be erroneously treated as monetary amounts (`1` paise) without explicit `not isinstance(x, bool)` filters.
- **Null-State Debugging:** Tested the `dict.setdefault()` trap in the Python REPL, confirming that `setdefault()` does not overwrite explicit `None` values already present in dictionary keys.
- **Refund Invariants:** Validated that cumulative proportional reversal $\lfloor \text{awarded} \times \text{total\_refunded} / \text{original\_amount} \rfloor$ preserves points parity across multiple partial refunds and that `delta` must be clamped to `max(0, out['points_balance'])`.
- **Test Execution:** Ran all 229 automated tests locally (`python3 -m pytest -v`) and verified the offline demo (`python3 -m main`).

## 3. Displayed Credits / Tokens
- **Tokens / Credits:** Not available (integrated developer session).

## 4. Suggestions Accepted, Modified, or Rejected
- **Accepted:** Using pure integer division throughout `calculate_points()` and `apply_reward_event()` rather than intermediate float conversions, avoiding precision loss in financial calculations.
- **Modified / Rejected:** An initial suggestion considered using shallow copies (`dict.copy()`) or in-place mutations for performance. This was rejected in favor of `deepcopy()` because caller accounts must remain strictly immutable as enforced by `test_event_processing_does_not_mutate_input_account`.
