# Approach and implementation decisions

## 1. Baseline

- Before editing, I ran `python -m pytest -q`.
- The untouched starter did not pass. The output showed failures involving point rounding at paise boundaries, a zero-point cap, event replay, and invalid or excessive refunds. The exact baseline pass/fail totals were not retained, so I have not guessed them.
- I ran `python -m main` after the changes. It printed:

  ```text
  Points example: 27
  Repeat warnings: []
  ```

  The points result follows the sample rules: `259900 // 10000 = 25` base points, then `25 * 110 // 100 = 27`. The repeat example has two matching transactions, which does not exceed the default threshold of two.

## 2. Codebase understanding

- I inspected `service.py`, `models.py`, `fixtures.py`, `main.py`, both files under `tests/`, the project pytest configuration, and the written requirements in `STUDENT_PROBLEM_STATEMENT.md`.
- `models.new_account` creates an account with a zero balance, a processed-event ID list, a transaction mapping, and a ledger list.
- `main.py` is an offline demonstration: it gets sample reward rules and transactions from `fixtures.py`, calls `calculate_points` and `flag_repeat_transactions`, and prints their results. It does not execute the test suite.
- `apply_reward_event` copies the account, then applies captured purchases or refunds to its transaction data, points balance, processed-event IDs, and ledger.
- `flag_repeat_transactions` groups transaction records by account, date, and amount, then reports groups whose size exceeds the threshold.
- I used the problem statement and visible tests as the behaviour contract. The tests specify floor-based point calculation, bonus-before-cap ordering, event replay handling, refund bounds, proportional reversals, and repeat thresholds.

## 3. Investigation and implementation strategy

### Point calculation

- **Symptom:** Boundary cases such as `9999` paise and `19999` paise produced too many points in the starter.
- **Hypothesis:** Converting the amount to a floating-point rupee value and calling `round` was rounding purchases up, but the requirement awards points only for complete 100-rupee units.
- **Evidence:** The acceptance tests expect `calculate_points(19999, 1) == 1` and `calculate_points(9999, 1) == 0`. The problem statement explicitly specifies `floor(amount_paise / 10000)`.
- **Fix:** Use integer floor division for the base, integer arithmetic for the bonus, and apply the optional cap afterward. Validate the numeric rule inputs and treat a cap of zero as an actual cap.

### Event replay and duplicate processing

- **Symptom:** Replaying a purchase with an existing transaction avoided a second award, but could still append the event ID repeatedly. The starter also did not make refund replay idempotent.
- **Hypothesis:** Idempotency must be enforced at the event boundary before applying any transaction changes.
- **Evidence:** The purchase replay test checks that the balance, processed IDs, and ledger remain unchanged on replay. The problem statement requires purchase and refund events to be processed once.
- **Fix:** Require a non-empty event ID, return without changes when that ID has already been processed, and record a new ID once before processing its event. A purchase also cannot create a second transaction record for an already-known transaction ID.
- **Regression coverage:** Added a test that replays a refund and checks the balance, refunded amount, processed IDs, and ledger count.

### Refund validation and reversals

- **Symptom:** The starter accumulated negative or excessive refund amounts without validating the total against the original purchase; repeated refund events could also affect the account more than once.
- **Hypothesis:** Refund amounts must be positive integers, and cumulative refunds must not exceed the purchase amount before any transaction or balance mutation occurs.
- **Evidence:** The acceptance tests include negative, zero, non-integer, and over-purchase refunds, as well as a partial refund. The written requirements also prohibit reversing more points than were awarded or creating a negative points balance.
- **Fix:** Validate the refund and transaction values before changing the transaction. Calculate the cumulative proportional reversal with integer arithmetic, cap it at the points awarded, and clamp the resulting balance at zero. Ledger entries record the reversal actually applied to the balance.

### Repeat-alert input handling

- **Symptom:** The repeat grouping code accepted records even when identifiers were absent, which could group unrelated or malformed records together.
- **Hypothesis:** A repeat alert is meaningful only when account, date, transaction identifier, and amount are usable.
- **Evidence:** The acceptance tests include missing grouping keys and distinct-account/date/amount cases.
- **Fix:** Skip malformed records, group valid rows by `(account_id, date, amount_paise)`, and retain the specified strict threshold rule: a group is reported only when its count is greater than the threshold.

## 4. Implementation decisions

- I kept the existing public functions and their responsibilities in `service.py`; no new runtime dependency or service layer was needed.
- I used integer arithmetic rather than floating-point rounding because amounts are in paise and the written rules define floor operations.
- I deep-copy the input account before applying an event. This preserves the existing non-mutation behaviour verified by the tests.
- I treated an invalid event identifier or transaction identifier as insufficient information to safely apply an event. Unknown event types do not award points.
- I kept repeat alerts informational: the function reports matching groups but does not block transactions or label customers as fraudulent.
- I added focused regression tests in `tests/test_contract.py` for refund replay, missing event IDs, and records missing repeat-group identifiers. Existing tests were left intact.
- I did not implement a separate optimization or change the demo interface; the task was to correct the required reward, refund, and alert behaviour without changing the existing API.

## 5. Verification

- **Python version:** `Python 3.14.7`.
- **Baseline command:** `python -m pytest -q` — failed on the untouched starter; see the limitation in the Baseline section for why no exact totals are given.
- **Final test command:** `python -m pytest -q` — `217 passed in 0.46s`.
- **Demo command:** `python -m main` — completed successfully and printed the output recorded in the Baseline section.
- **Syntax and diagnostics:** Pylance reported no syntax errors and no diagnostics for `service.py`.
- **Edge cases covered by the final suite:** just-below and exact 100-rupee boundaries; negative amounts and invalid rules; zero cap; purchase and refund replay; missing event identifiers; partial and excessive refunds; invalid refund values; unknown transactions; empty or distinct repeat groups; and missing repeat identifiers.
- **Known limitation:** The event processor relies on the account structure returned by `new_account` (or an equivalent mapping with the expected list/dictionary fields). It is an in-memory example, not a persistent or concurrency-safe payment ledger.
