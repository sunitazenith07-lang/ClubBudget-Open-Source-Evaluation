# approach.md - Required submission

## 1. Baseline
- Commands run before editing: `python -m pip install -r requirements-dev.txt`, `python -m pytest -q`, `python main.py`
- Initial test result: `45 failed, 169 passed in 1.00s`
- Demo/output observed: `Points example: 27`, `Repeat warnings: []`

## 2. Codebase understanding
- Important files/functions inspected: `models.py` (`new_account`), `service.py` (`calculate_points`, `apply_reward_event`, `flag_repeat_transactions`), `fixtures.py`, `tests/test_contract.py`, `tests/test_acceptance_matrix.py`, `STUDENT_PROBLEM_STATEMENT.md`.
- Rewards calculation, refund, ledger or alert flow traced: purchase events create transactions and award points; refunds update `refunded_paise`, recompute proportional reversal, update balance and ledger; repeat alerts group transactions by account/date/amount.
- How you confirmed understanding: traced starter code against problem statement rules and reproduced all 45 failures with pytest.
- we used ai agents to run some of the test cases like claude opus 4.

## 3. Investigation and implementation strategy
- Issue 1: Duplicate event IDs. Symptom: replaying a purchase appended `event_id` twice and failed `processed_event_ids == [event_id]`. Evidence: `test_purchase_event_replay_is_idempotent`. Fix: return account unchanged when `event_id` is already in `processed_event_ids`.
- Issue 2: Unbounded refunds. Symptom: invalid/excess refunds changed `refunded_paise` and balance. Evidence: `test_invalid_or_excess_refund_does_not_change_account`. Fix: validate amount type, positivity, original amount, and cumulative refund limit before applying.
- Issue 3: Ledger/mutation and alert safety. Symptom: non-captured events could alter state; malformed inputs could crash. Evidence: contract and acceptance tests. Fix: only process captured purchases and valid refunds, deepcopy input, and guard `flag_repeat_transactions` against empty/invalid input by using ai tools (Antigravity, claude).

## 4. Implementation decisions
- Main changes and why: rewrote validation and control flow in `service.py` to enforce integer arithmetic, idempotency, refund bounds, proportional reversal, and safe repeat grouping.
- Alternatives considered and why rejected: keeping per-event append for all event types was rejected because it violated idempotency and account-unchanged expectations for invalid events.
- Assumptions: refund amounts are in paise; invalid refund events are ignored entirely; missing identifiers are handled defensively.

## 5. Verification
- Tests added or changed: added `tests/test_regression.py` with 7 regression tests; existing tests retained.
- Commands run and actual results: `python -m pytest -q` -> `214 passed in 0.58s`; `python main.py` -> successful output.
- Edge cases verified: replay events, invalid/excess refunds, boundary refund amounts, negative/invalid rules, empty and malformed repeat inputs.
- Remaining failures or known limitations: none for code tests; documentation files still need final manual completion if required by submission.

Record actual engineering decisions and evidence. Do not claim tests or experiments you did not run.