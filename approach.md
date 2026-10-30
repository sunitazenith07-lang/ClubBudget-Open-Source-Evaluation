# Approach

Implementation, regression tests, and these notes were prepared with GitHub Copilot assistance. The commands and results below are the observed local run outputs.

## 1. Baseline
- Before editing, ran `& .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt` in the ignored `.venv` using Python 3.14.7; pytest was 9.2.0.
- Baseline `& .\.venv\Scripts\python.exe -m pytest -q`: **67 failed, 147 passed** (214 total).
- Baseline `& .\.venv\Scripts\python.exe -m main`: `Points example: 28`; `Repeat warnings: []`.

## 2. Codebase understanding
- Read the project brief, README, student checklist, contribution guide, source modules, both visible test files, workflow files, pull-request template, documentation templates, and dataset schema/content.
- The demo in `main.py` calls `calculate_points` and `flag_repeat_transactions` in `service.py`; reward-event processing also lives in `service.py`. `models.py` creates the account state consumed by that function, and `fixtures.py` supplies the demo input.
- Parsed `data/records.json`: 40 accounts, 180 transactions, 264 reward events, 180 captured purchases, 8 rule cases, and 10 edge-case categories.

## 3. Investigation and implementation strategy
- Points were calculated with `round(amount_paise / 10000)`, which converted to float and rounded paise near rupee boundaries upward. A truthiness check on `cap_points` also ignored a zero cap. Replaced these with integer floor arithmetic and explicit rule validation.
- Replayed event IDs were appended without checking for an earlier occurrence. Refunds also mutated cumulative totals before validating amount/type/bounds. Added event-ID checks and accept only positive integer refunds that fit within the remaining original amount.
- Proportional reversals now use the cumulative refunded amount, so multiple partial refunds share the same integer-floor rule as one combined refund. Ledger entries record identifiers, amount, point delta, and resulting balance.
- Repeat grouping now skips rows without usable identifiers or valid amounts and does not count a repeated transaction ID twice.

## 4. Implementation decisions
- Kept the public function signatures and dictionary-based model unchanged to match the starter and tests.
- Used integer arithmetic throughout; booleans are rejected as integer amounts/rules because Python treats `bool` as a subclass of `int`.
- Invalid event identifiers are not accepted or recorded. A valid but unrecognized event has no balance or ledger effect; event IDs are tracked to prevent reprocessing.
- Did not add a persistence layer, external dependency, or optional stretch feature; those would exceed the offline starter’s scope.

## 5. Verification
- Added regressions for malformed rule types, missing event IDs, duplicate refund delivery and ledger contents, cumulative partial-refund rounding/over-refund, and invalid/duplicate repeat IDs.
- Final `& .\.venv\Scripts\python.exe -m pytest -q`: **219 passed**.
- Final `& .\.venv\Scripts\python.exe -m main`: `Points example: 27`; `Repeat warnings: []`.
- No known test failures. No performance benchmark was run.