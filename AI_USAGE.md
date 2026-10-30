# AI Usage Declaration

| Tool / model | What it was used for |
|---|---|
| Claude Code (desktop app), model Claude Opus 5.5 (`claude-opus-5-5`) | Reviewing the repository and dataset, assisting with changes in `service.py`, writing regression tests in `tests/test_regressions.py`, and running the test suite. |

- Why: AI tools were used in accordance with the evaluator's guidelines permitting AI assistance, provided its use was disclosed.
- Verification: I independently re-ran `python -m pytest -q` and confirmed that all 249 tests passed. I also manually checked the 259900-paise example (25 → 125 → 156 points) against the reward calculation and reviewed `service.py` to understand the implemented changes.
- Modified: An initial test expectation for `test_bonus_over_100_percent_then_cap` was corrected from 22 to 225 after checking the calculation (300000 paise → 30 units × 3 = 90 → 90 × 250 // 100 = 225).
- Accepted with an assumption: Zero-amount transactions were excluded from repeat alerts, resulting in 48 groups instead of 60. This assumption is documented in `REWARD_RULE_NOTES.md`.
- Credits / tokens: Not available.
- Secrets / personal data: None used. All data was synthetic repository data.