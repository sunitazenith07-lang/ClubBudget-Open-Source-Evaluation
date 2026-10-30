# AI-Use Declaration

## Tools, models, and sources used
- **Tool/Model:** Antigravity (powered by Gemini 3.8 Flash).
- **Purpose of use:** Codebase inspection, baseline defect tracing, running automated test suites, drafting regression tests, and generating documentation artifacts following repository guidelines.
- **Independent verification & modifications:**
  - Independently verified all Python arithmetic by executing manual calculations and automated pytest suites (`221 passed in 0.05s`).
  - Audited type handling in Python, specifically verifying that `bool` is a subclass of `int` and implementing explicit guards (`not isinstance(val, bool)`) to prevent `True`/`False` from being processed as numbers.
  - Formulated edge cases for cumulative proportional refund reversals and verified mathematically against edge cases in `data/records.json`.
- **Displayed credits / tokens:** Not available in this local runtime environment.
- **Suggestion evaluated (accepted / modified / rejected):**
  - *Suggestion considered:* Converting `processed_event_ids` to a Python `set` in `models.py` for $O(1)$ lookup performance.
  - *Decision / Reason:* **Rejected.** Converting `processed_event_ids` to a `set` would break the public data model contract, break existing assertions in `tests/test_contract.py` that check for exact ordered list equality (`['E1']`), and compromise standard JSON serialization. Kept as an ordered list while noting the hybrid internal set as a future architectural improvement.
