# approach.md

## 1. Baseline
- Commands run: python -m pip install -r requirements-dev.txt, python -m pytest -q, python -m main
- Initial test result: [paste your first "X failed, Y passed" line]
- Demo output: [what python -m main printed]

## 2. Codebase understanding
- Files I looked at: service.py, tests/, main.py, fixtures.py, models.py
- Flow: a purchase gets points from calculate_points, is saved as a transaction, adds to the balance and writes a ledger entry. A refund reverses points in proportion and writes a negative ledger entry. Repeat alerts group transactions by account, date and amount.
- How I checked: I ran the tests, read the failing assertions and tried small examples by hand.

## 3. Issues and fixes
- Issue 1: calculate_points used float division (/), so 19,999 paise gave 1.9999 hundreds. I changed it to floor division (//).
- Issue 2: the same event_id could be processed twice and change the balance twice. I now return early if the event_id is missing or already processed.
- Issue 3: refunds were not validated. Zero, negative, non-integer or too-large refunds were accepted. I now ignore a refund unless it is an int, greater than 0 and within the amount still refundable.

## 4. Decisions
- Main changes: the three fixes above, kept small.
- Rejected: capping a too-large refund (the test expects it to be ignored) and changing > to >= in the repeat alerts (the tests showed > was right).
- Assumptions: an invalid refund changes nothing, and a bool is not a valid amount.

## 5. Verification
- Tests added: [your tests, or "none"]
- Result: python -m pytest -q -> [final summary line]
- Edge cases checked: replayed event, refund of 0, negative refund, refund larger than the purchase, partial refunds, amount just below a 100-rupee boundary.
- Known limits: [none, or what is left]