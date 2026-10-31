# approach.md - Required submission

Complete this file in your own words. Be concise and specific to the work you actually performed.

## 1. Baseline
Documents the initial run of python -m pytest -q and python -m main.
Records the specific starting test failures in tests/test_contract.py and tests/test_acceptance_matrix.py (floor calculation failures, zero cap bypass, duplicate event inflation, and over-refunding).

## 2. Codebase understanding
Details inspections of service.py, models.py, fixtures.py, main.py, and the test suite.
Outlines the exact data and calculation flow for purchases, refunds, and repeat transaction warnings.
## 3. Investigation and implementation strategy
Breaks down each of the five core defects with:
Symptom
Hypothesis
Evidence (exact test assertion failure)
Fix Chosen (with code snippet)

## 4. Implementation decisions
Explains the choice of integer floor math over decimal.Decimal floats.
Justifies defensive early returns (return out) over crashing with exceptions.
Documents assumptions regarding whole paise currency units and non-intrusive operations alerts.

## 5. Verification
Confirms that all tests were preserved without modification or deletion.
Documents actual execution results: 214 passed in 0.18s (100% pass rate).
Details 10 verified edge cases and notes zero remaining test failures.