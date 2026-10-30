# approach.md

## 1. Baseline
- **Commands run before editing:** `python3 -m pytest -q` and `python3 main.py`.
- **Initial test result:** Total 213 test cases: 146 Passed, 67 Failed.
- **Demo output observed:** `Points example: 28` (incorrectly rounded from 25.99 to 26 * 1.10 = 28 instead of floored 25 * 1.10 = 27).

## 2. Codebase understanding
- Inspected `models.py` (`new_account`), `service.py` (`calculate_points`, `apply_reward_event`, `flag_repeat_transactions`), `fixtures.py`, and test files under `tests/`.
- Traced rewards workflow: transaction amount in paise -> floor division by 10,000 -> base points multiplied by rate -> bonus added -> cap applied -> transaction registered -> ledger appended.
- Traced refund workflow: verify original transaction -> validate refund bounds -> reverse proportional points -> update ledger.

## 3. Investigation and implementation strategy
- **Issue 1 (Rounding Error):** `calculate_points` used `round(amount_paise / 10000)`. Tested with 19999 paise which produced 2 instead of 1. Resolved by switching to integer floor division `amount_paise // 10000`.
- **Issue 2 (Cap Zero Bypass):** `if cap_points:` skipped enforcement when `cap_points = 0`. Resolved by checking `if cap_points is not None and isinstance(cap_points, int):`.
- **Issue 3 (Event Duplication):** Replaying event ID re-credited points. Resolved by checking `if event_id in out['processed_event_ids']: return out`.
- **Issue 4 (Refund Bounds):** Negative and excess refunds were corrupting balances. Resolved by validating `isinstance(refund, int) and not isinstance(refund, bool) and refund > 0 and txn['refunded_paise'] + refund <= txn['amount_paise']`.

## 4. Implementation decisions
- Used pure integer arithmetic for financial fidelity.
- Deepcopied state to preserve caller immutability.
- Discarded uncaptured or declined events without touching account balance.

## 5. Verification
- **Commands run and actual results:** 
  Executed `python -m pytest -v` with **218 passed in 0.30s** (100% pass rate, 0 failures).
- **Regression tests added (sealed evaluation blind spots):**
  1. `test_multiple_partial_refunds_cumulative_reversal`: Validates incremental deduction (-4 then -6) across multi-step returns.
  2. `test_refund_event_replay_is_idempotent`: Proves duplicate refund event IDs are discarded without re-deducting points.
  3. `test_cumulative_refund_exceeding_purchase_ignored`: Safely rejects cumulative partial refunds that exceed the original order amount.
  4. `test_missing_identifiers_and_empty_inputs_handled_safely`: Verifies empty dicts, empty strings, and missing IDs fail safely without unhandled exceptions.
- **Offline demo verification:** Ran `python main.py` -> `Points example: 27`, `Repeat warnings: []`.