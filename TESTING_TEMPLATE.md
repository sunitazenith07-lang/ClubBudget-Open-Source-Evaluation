# Testing notes

The challenge-specific completed record is [TESTING.md](TESTING.md). Generic search/filter scenarios do not apply to this offline rewards service.

| Scenario | Input | Expected | Actual | Result |
|---|---|---|---|---|
| Purchase boundary | 19,999 paise, rate 1 | 1 point | 1 | Pass |
| Bonus/cap | 50,000 paise, rate 2, 50% bonus, cap 6 | 6 | 6 | Pass |
| Invalid refund | 150,000 refund on 100,000 purchase | Balance 10, refund total 0 | Matches | Pass |
| Domain transition | 50,000 refund after 100,000 capture | Balance 5, reversal 5 | Matches | Pass |
| Empty/missing IDs | Empty event | Balance 0 | 0 | Pass |

## Automated run
- Python 3.12.14 / pytest 9.2.0; command: `python -m pytest -q` (environment setup in TESTING.md).
- Total: 219
- Passed: 219
- Failed: 0
- Errors: 0
- Skipped: 0

Verified during AI-assisted submission preparation, not claimed as the original author's pre-edit run. Reconstructed starter: 67 failed, 147 passed.
