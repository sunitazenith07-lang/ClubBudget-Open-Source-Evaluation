# optimizations.md - Required submission

Document optimizations you considered or implemented. Do not claim a speedup or improvement unless you measured it.

## 1. Baseline and objective
- What needed improvement (correctness, clarity, complexity, memory, repeated work, maintainability)?

The main objective was to improve the correctness, reliability, and maintainability of the RewardBook system.
The initial implementation had issues with floating-point rounding, duplicate event processing, and refund validation.

- What evidence suggested an improvement could help?

The test results showed that improvements were needed in reward calculation and transaction handling.

## 2. Options considered
Describe each option's expected benefit and risk, including rejected ideas.

Floating-point arithmetic vs integer arithmetic:
Integer arithmetic was selected because it avoids floating-point rounding issues in reward calculations.
Floating-point rounding was not preferred for financial calculations.

Duplicate event handling:
Checking previously processed event IDs helps prevent duplicate processing.
Processing every event without checking its ID could cause incorrect transaction records.

Refund validation:
Validating refund amounts before updating transactions helps prevent invalid and excessive refunds.
Accepting all refund values could lead to incorrect balances.

## 3. Changes implemented
- Change and reason:
    Changed reward calculation to use integer floor division.
    Added validation for negative and invalid reward inputs.
    Added support for an optional points cap, including a zero cap.
    Added duplicate event ID checking.
    Improved refund amount validation.

- Tests that protect correctness:
Existing automated pytest tests.
Reward calculation boundary cases.
Duplicate purchase event cases.
Invalid refund input cases.

- Measurement method and result (only if measured):
    No separate performance benchmark was conducted.
    Final automated test result: 214 passed in 0.70 seconds.

## 4. Trade-offs
Explain trade-offs involving clarity, correctness, performance, memory, or maintainability.
Integer arithmetic improves calculation correctness but requires careful handling of rounding rules.
Additional validation makes the code more reliable but adds conditional checks.
Duplicate event checking improves transaction reliability but requires maintaining processed event IDs.
Refund validation adds complexity but protects transaction and reward balances.

## 5. Further improvements
What would you do next with more time, and how would you validate it?
Testing larger transaction datasets.
Investigating memory usage when storing many processed event IDs.
Adding more tests for multiple partial refunds.
Reviewing ledger consistency for unusual transaction sequences.

If you made no optimization change, state that honestly and compare at least two reasonable options. Correctness and maintainability take priority over unnecessary complexity.