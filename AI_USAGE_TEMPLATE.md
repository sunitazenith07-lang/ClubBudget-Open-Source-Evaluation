# AI-Use Declaration

- **Tool/Model:** Antigravity AI Assistant (Gemini model).
- **Purpose of Use:** Guided codebase navigation, test execution, identifying root cause of test failures, and generating regression test templates.
- **Independent Verification:**
  - Traced and validated every mathematical formula (`amount // 10000`, `bonus_points`, `should_reverse`) directly against the written problem statement specifications.
  - Independently tested and verified Python boolean inheritance edge case (`isinstance(True, int)`).
  - Executed baseline tests and verified all 221 tests locally (`python -m pytest -q`).
- **Displayed Credits/Tokens:** Not available.
- **Suggestion Accepted / Modified:**
  - *Modified:* The suggestion to use incremental delta calculations for partial refunds was modified to cumulative tracking (`should_reverse = (txn['awarded_points'] * new_refunded) // txn['amount_paise']`) to eliminate integer truncation drift across multiple partial refunds.

