# AI Usage Declaration

| Tool / model | What it was used for |
|---|---|
| Claude Code (desktop app), model Claude Opus 5.5 (`claude-opus-5-5`) | Reviewing the repository and dataset; making the changes in `service.py` and `main.py` (core fixes, the configurable threshold stretch item, the list/dict ID fixes found by stress testing, the threshold-fallback and duplicate-ID fixes, and the refund-clamp, non-dict account and set-based alert ID fixes found by extreme stress testing); writing the tests in `tests/test_regressions.py`, `tests/test_threshold_config.py` and `tests/test_stress.py`; drafting `approach.md`, `challenges.md`, `optimizations.md`, `TESTING.md`, `REWARD_RULE_NOTES.md`, `ARCHITECTURE.md`, `PROJECT_NOTES.md` and the PR description; running the test suite, the randomized stress runs and the extreme stress run; triggering the GitHub Actions run on my fork; and git commits/pushes. |

- Why: AI tools were used in accordance with the evaluator's guidelines permitting AI assistance, provided its use was disclosed.
- Verification: the full suite (`python -m pytest -q`) passes: 326 tests locally on Python 3.14.7. The last GitHub Actions run on Python 3.11 (at 319 tests, before the extreme-stress fixes) showed 319 passed, 0 failed. I also manually checked the 259900-paise example (25 → 125 → 156 points) against the reward calculation and reviewed `service.py` to understand the implemented changes.
- Modified: An initial test expectation for `test_bonus_over_100_percent_then_cap` was corrected from 22 to 225 after checking the calculation (300000 paise → 30 units × 3 = 90 → 90 × 250 // 100 = 225).
- Modified: A dataset figure in the docs ("157 events without an `event_id`") was wrong; a recount showed 9, and the docs were corrected.
- Accepted with an assumption: Zero-amount transactions were excluded from repeat alerts, resulting in 48 groups instead of 60. This assumption is documented in `REWARD_RULE_NOTES.md`.
- Credits / tokens: Not available.
- Secrets / personal data: None used. All data was synthetic repository data.
