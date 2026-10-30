# AI-Use Declaration

List each tool/model or source, why you used it, what you independently verified or changed, any displayed credits/tokens (or “not available”), and one suggestion accepted, modified or rejected with your reason. Never include secrets or private personal data.

- **Tool / model and sources used**: Antigravity coding assistant (Gemini) and Python 3.14 / `pytest` documentation.
- **Why used**: Used to inspect failing tests, review edge cases in `service.py` and `tests/test_contract.py`, and format Markdown documentation files.
- **What was independently verified or changed**: Verified all 218 tests locally with `py -m pytest -q` (`218 passed in 0.17s`) and `py -m main` (`Points example: 27`), verified the exact parametrized input counts in `tests/test_acceptance_matrix.py` (15 inputs in `test_invalid_or_excess_refund_does_not_change_account` and 20 inputs in `test_refund_amount_bounds_and_balance` of which 10 are excess refunds), and verified cumulative partial refunds, duplicate event replay, and excess refund rejection in `test_refund_event_replay_and_cumulative_partial_refunds`.
- **Displayed credits / tokens**: Not available.
- **Suggestion accepted, modified, or rejected**: Rejected changing `processed_event_ids` from a `list` to a `set` because `tests/test_contract.py` and `tests/test_acceptance_matrix.py` explicitly assert `processed_event_ids == ['E1']` as a `list`; also corrected documentation to cite the exact executed command `py -m pytest -q` and exact parametrized test counts.
