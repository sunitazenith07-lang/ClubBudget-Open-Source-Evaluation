# optimizations.md - Required submission

Document optimizations you considered or implemented. Do not claim a speedup or improvement unless you measured it.

## 1. Baseline and objective
- What needed improvement (correctness, clarity, complexity, memory, repeated work, maintainability)?
  The starter code had bugs causing 67 test failures. Fixing correctness was the priority.

- What evidence suggested an improvement could help?
  Test suite showed specific failure patterns indicating which rules were broken.

## 2. Options considered
Describe each option's expected benefit and risk, including rejected ideas.

- Option 1: Hard-code test expected values
  **Benefit:** Tests would pass immediately
  **Risk:** Would not fix actual business logic; would break with different inputs; unethical

- Option 2: Use floating-point arithmetic
  **Benefit:** Simpler code
  **Risk:** Violates integer arithmetic requirement; causes floating-point precision errors; would fail floor/cap tests

- Option 3: Fix root causes with proper integer arithmetic
  **Benefit:** All tests pass correctly; matches specification; maintainable
  **Risk:** More code changes needed; but this was the correct approach

## 3. Changes implemented
- Change and reason:
  Fixed `calculate_points()` to use `//` floor division instead of `round()`.
  Fixed `cap_points=0` being ignored by changing condition to `if cap_points is not None:`.
  Fixed `apply_reward_event()` to handle event deduplication and refund validation.

- Tests that protect correctness:
  All 214 tests now pass, including edge cases for floor, cap, bonus, and refund scenarios.

- Measurement method and result (only if measured):
  Not measured execution time; correctness was verified by test suite passing.

## 4. Trade-offs
Explain trade-offs involving clarity, correctness, performance, memory, or maintainability.

- Correctness vs. simplicity: The fixed code is slightly more verbose but correctly handles all edge cases.
- Integer vs. floating-point: Using integer arithmetic is required by specification and avoids precision issues.
- Performance: No significant difference for this use case; correctness is the priority.

## 5. Further improvements
What would you do next with more time, and how would you validate it?

- Add more edge case tests for boundary values
- Make the repeat threshold configurable as stretch work
- Generate CSV account statements for user reporting
- Add type hints for better maintainability

If you made no optimization change, state that honestly and compare at least two reasonable options. Correctness and maintainability take priority over unnecessary complexity.