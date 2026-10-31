# Implementation notes

> **AI-use disclosure:** AI assistance was used with evaluator permission, as confirmed by the requester. See [AI_USAGE.md](AI_USAGE.md) for details.

## 1. Baseline

- Environment: Python 3.13.15.
- Commands run from `RewardBook-Open-Source-Evaluation` before editing:
  - `python -m pytest -q`: **67 failed, 147 passed**.
  - `python -m main`: `Points example: 28`; `Repeat warnings: []`.

## 2. Codebase understanding

- `main.py` calls `calculate_points` and `flag_repeat_transactions` using example rules and transactions from `fixtures.py`.
- `new_account` in `models.py` initializes a balance, processed-event IDs, transaction map, and ledger.
- `apply_reward_event` in `service.py` copies the account, handles purchase captures and refunds, and records point deltas.
- `tests/test_contract.py` and `tests/test_acceptance_matrix.py` state the expected floor calculation, cap, replay, refund, and alert behavior. `data/records.json` contains synthetic edge cases, including missing IDs and malformed refund amounts.

## 3. Defects and evidence

1. **Point calculation:** the implementation rounded a floating-point rupee conversion. The boundary tests failed, including 9,999 paise and 19,999 paise. It now floors with integer division before applying the points rate, bonus, and cap.
2. **Caps and invalid rules:** a truthiness check skipped a cap of zero. It now applies any non-`None` valid cap, and invalid/negative or non-integer numeric values return zero points.
3. **Event processing and refunds:** repeated refund event IDs could change state repeatedly, and separate refunds could exceed the purchase amount. Event IDs are checked for replay, cumulative refunds are bounded by the purchase, and proportional reversals use integer arithmetic.
4. **Malformed alert rows:** repeat grouping now ignores malformed rows and duplicate transaction IDs. A zero threshold retains its original mathematical behavior; negative thresholds are rejected.

## 4. Implementation decisions

- Kept the existing module API and account/ledger data shape; no dependency or storage changes were needed.
- Used small input-validation helpers and integer arithmetic instead of floating-point rounding.
- Preserved copy-on-write account updates and kept alerts review-only.
- Assumption: malformed or incomplete purchase/refund input does not mutate balances or transactions. Valid event IDs are retained in the processed-ID list before later event validation, preventing reuse of the same ID with a changed payload.

## 5. Verification

- Added regression tests in `tests/test_acceptance_matrix.py` for invalid rules, refund replay, cumulative refunds, missing event IDs, invalid account balances, malformed/duplicate alert rows, and threshold zero.
- Final `python -m pytest -q`: **221 passed**.
- Final `python -m main`: `Points example: 27`; `Repeat warnings: []`.
- `git diff --check` passed.
- No pull request or CI run has been completed.
