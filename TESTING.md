## Test command and environment
- Python version:Python 3.14.6
- Command run:python -m pytest -q
- Actual test summary:47 failed, 167 passed

## What I Did
  - Before: `round(amount_paise / 10000)`
  - After: `amount_paise // 10000`
  - This made a few test cases pass :/
