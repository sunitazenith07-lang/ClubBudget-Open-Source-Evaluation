# approach.md

## 1. Baseline
- Commands run: python -m pip install -r requirements-dev.txt, python -m pytest -q, python -m main
- Initial test result: the starter tests had failures (I did not save the exact count)
- Demo output: [run python -m main and write one line about what it printed]

## 2. Codebase understanding
- Files I looked at: service.py, tests/, main.py, fixtures.py, models.py
- Flow: a purchase gets points from calculate_points, is saved as a transaction, adds to the balance and writes a ledger entry. A refund reverses points in proportion and writes a negative ledger entry. Repeat alerts group transactions by account, date and amount.
- How I checked: I ran the tests, read the failing assertions and tried small examples by hand.

## 3. Issues and fixes
- Issue 1: calculate_points used round(amount_paise / 10000), so 19,999 paise rounded up to 2 hundreds instead of flooring to 1. I changed it to amount_paise // 10000.
- Issue 2: `if cap_points:` treated a cap of 0 as "no cap". I changed it to `if cap_points is not None:`, so a cap of 0 gives 0 points.
- Issue 3: the same event_id could be processed twice and change the balance twice. I now return early if the event_id is missing or already processed, and unknown event types are ignored.
- Issue 4: refunds were not validated. I now ignore a refund unless it is an int, greater than 0 and within the amount still refundable.

## 4. Decisions
- Main changes: the four fixes above, kept small.
- Rejected: capping a too-large refund (the tests expect it to be ignored) and changing > to >= in the repeat alerts (the tests showed > was right).
- Assumptions: an invalid refund changes nothing, and a bool is not a valid amount.

## 5. Verification
- Tests added: none
- Result: python -m pytest -q -> 214 passed in 0.87s
- Edge cases checked: replayed event, refund of 0, negative refund, refund larger than the purchase, wrong-type refund, amount just below a 100-rupee boundary, cap of 0.
- Known limits: none known. A purchase with no transaction_id is not rejected explicitly.