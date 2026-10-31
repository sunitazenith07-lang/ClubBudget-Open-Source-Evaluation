# AI-Use Declaration

Tool/model used: AI coding assistant (github copilot) used to inspect repository files, run tests, propose and apply edits to `service.py`, and draft documentation/PR text.
Why used: To accelerate code inspection, reproduce the 45 failures, implement fixes, and verify the full test suite.
Independently verified/changed: I ran `python -m pytest -q` before and after changes (45 failed → 214 passed), ran `python main.py`, manually replayed purchase/refund events, and checked invalid-refund account equality. I reviewed and adjusted all generated code and documentation to match the repository tests and problem statement.
- Displayed credits/tokens: Not available in this environment.
- One suggestion accepted/modified/rejected: Accepted the assistant’s suggestion to add event-id idempotency early returns; modified it to only deduplicate non-None event IDs and to avoid appending event IDs for invalid/unknown events, so invalid refunds leave the account unchanged.