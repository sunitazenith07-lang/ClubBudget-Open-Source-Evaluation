# optimizations.md - Required submission

Document optimizations you considered or implemented. Do not claim a speedup or improvement unless you measured it.

## 1. Baseline and objective
- What needed improvement (correctness, clarity, complexity, memory, repeated work, maintainability)?
The main objective was to improve correctness, code clarity, and maintainability.

- What evidence suggested an improvement could help?
The initial test result was 67 failed and 147 passed out of 214 tests. Failures showed issues with rounding, zero caps, duplicate events, and refund calculations.

## 2. Options considered
Describe each option's expected benefit and risk, including rejected ideas.
Integer arithmetic: Chosen because it avoids floating-point rounding errors. It also keeps calculations accurate in paise.

Using round(): Rejected because it can incorrectly round purchase amounts near ₹100 boundaries.

Checking cap_points directly: Rejected because it treats zero as false.

Using cap_points is not None: Chosen because it correctly handles zero as a valid cap.

Adding complex caching: Not chosen because the project did not show a need for it.

## 3. Changes implemented
- Change and reason:
Replaced floating-point rounding with integer floor division (//).

Added proper zero-cap validation.

Added duplicate event checking using processed_event_ids.

Improved refund validation and cumulative point reversal.
- Tests that protect correctness:
Purchase amount boundary tests.

Zero-cap tests.

Duplicate event tests.

Full, partial, and excessive refund tests.

Invalid event tests.
- Measurement method and result (only if measured):
Ran python -m pytest -q.

Initial result: 67 failed, 147 passed.

Final result: 214 passed in 0.15s.

No separate performance benchmark was conducted, so no speedup is claimed.

## 4. Trade-offs
Explain trade-offs involving clarity, correctness, performance, memory, or maintainability.
Integer arithmetic improves calculation accuracy but requires careful handling of division.

Additional validation makes the code more reliable but adds some conditions.

deepcopy helps preserve the original account data but may use extra memory for larger account records.

The implementation prioritizes correctness and maintainability over unnecessary performance complexity.

## 5. Further improvements
What would you do next with more time, and how would you validate it?
With more time, I would:

Test the system with larger transaction histories.

Measure execution time and memory usage with larger datasets.

Explore whether copying only the required account data could reduce memory usage.

Add more tests for unusual event and refund combinations.
If you made no optimization change, state that honestly and compare at least two reasonable options. Correctness and maintainability take priority over unnecessary complexity.
Any future optimization would be benchmarked before claiming a performance improvement.