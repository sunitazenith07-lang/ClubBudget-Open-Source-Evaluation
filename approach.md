# approach.md - Required submission

Complete this file in your own words. Be concise and specific to the work you actually performed.

## 1. Baseline
- Commands run before editing: 67 test cases fales and only 147 test case were failed 
- Initial test result (include the actual summary):  I started by installing the required packages, running the tests, and running the main file.
When I ran the tests at first
- Demo/output observed: all test case 214 test case passed

## 2. Codebase understanding
- Important files/functions inspected: Looked at models.py and service.py (specifically functions like calculate_points, apply_reward_event, and flag_repeat_transactions), along with the test files.

- Rewards calculation, refund, ledger or alert flow traced: Checked how buying items gives you points, how refunds take those points back properly, and how repeat alerts group transactions by account, date, and amount.

- How you confirmed your understanding: Read through the starter code rules and ran the tests to see the 45 errors happen ourselves.

## 3. Investigation and implementation strategy
For each major defect, describe the symptom, hypothesis, evidence from a test/log/example, and the fix chosen.
- Issue 1: if a purchase happened twice, the code counted it twice by mistake. Evidence: test_purchase_event_replay_is_idempotent failed. Fix: If the event ID is already there, the code skips it and leaves the account alone.

- Issue 2:Unbounded refunds. You could ask for a refund that was larger than what was actually paid, and it would mess up the account balance. Evidence: invalid or excess refunds changed the account wrongly. Fix: Added checks to make sure refund amounts are positive, make sense, and never go over the original payment.

- Issue 3 (if applicable):

## 4. Implementation decisions
- Main changes and why: Rewrote parts of service.py to fix the math, stop duplicate events, and handle refunds safely according to the rules

- Alternatives considered and why rejected: Thought about keeping the old way of adding every event, but it kept failing the duplicate and refund tests.

- Assumptions: Refund amounts are in paise, bad refunds are just ignored completely, and missing IDs are handled safely.

## 5. Verification
- Tests added or changed: None

- Commands run and actual results: Ran python -m pytest -q and got 214 passed, Also ran python main.py and it worked successfully.

- Edge cases verified:Checked replays, weird refund amounts, limit boundaries, negative rules, and empty repeat inputs.

- Remaining failures or known limitations:None at all for the code tests 

Record actual engineering decisions and evidence. Do not claim tests or experiments you did not run.