# optimizations.md - Required submission

Document optimizations you considered or implemented. Do not claim a speedup or improvement unless you measured it.

## 1. Baseline and objective
Things to fix: Accuracy of points, making sure running things twice doesn't mess up, refund limits, keeping records correct, and safe inputs.

Proof: 45 failing tests in test_acceptance_matrix.py and test_contract.py.

## 2. Options considered
Idea 1: Keep the old setup and just patch the obvious bugs. (Safe and easy, but left holes.)
Idea 2: Rewrite the logic with proper checks. (Took more code, but much safer and cleaner.)
What we threw out: Keeping every single event ID saved forever. It broke our rules for running things twice safely and keeping account balances stable.

## 3. Changes implemented
- Change and reason:
- Tests that protect correctness: Added checks for refunds
- Measurement method and result (only if measured): All 214 tests pass now
## 4. Trade-offs
Adding more checks makes it way stronger, but makes the code a bit longer.
Being strict about whole numbers means it will reject decimals. That's fine since our system only uses whole numbers anyway.

## 5. Further improvements
Add property-based testing to test refunds and duplicate runs in random ways
Add schema checks for events if we ever add more features to the API
If you made no optimization change, state that honestly and compare at least two reasonable options. Correctness and maintainability take priority over unnecessary complexity.