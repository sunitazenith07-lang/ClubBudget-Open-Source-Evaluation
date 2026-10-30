# challenges.md - COMPULSORY submission

This file is mandatory and worth 5 marks. Describe your actual experience honestly. Do not invent difficulties to fill the page.

## 1. Challenge or confusing behaviour
The most confusing behavior was understanding why purchase points calculations and refund events failed initially despite seemingly correct arithmetic formulas in the starter code. Specifically, floating-point rounding discrepancies during integer conversions and unexpected runtime `TypeError` crashes when malformed refund inputs (`None`, strings, or lists) were passed during edge-case tests.

## 2. Evidence
Running the initial baseline test suite (`python3 -m pytest -q`) yielded 67 failures. Key error tracebacks included `TypeError: unsupported operand type(s) for +=: 'int' and 'NoneType'` during refund processing, and assertion errors on point caps (such as `cap_points=0` being incorrectly bypassed because `0` evaluated as falsy).

## 3. What I tried
- Inspected test failure tracebacks to pinpoint which specific input variations triggered the `TypeError`.
- Traced the `calculate_points` function to observe how Python's built-in `round()` function handled fractional amounts (e.g., `19999` paise) compared to strict integer floor division.
- Tested conditional evaluation behavior for `cap_points` to verify why a zero cap was ignored.

## 4. Resolution
- **Root Cause:** The starter code relied on `round()` instead of strict integer floor division (`//`), and treated falsy values incorrectly for zero-caps. Additionally, it lacked type guards and boundary validation for incoming refund amounts.
- **Fix:** Replaced rounding with `// 10000`, updated the cap check to explicitly verify `is not None`, added input type validation (`isinstance(..., int) and not isinstance(..., bool)`), and implemented strict refund boundary limits. This fixed the root cause by ensuring precise integer calculations and graceful type rejection instead of masking symptoms.

## 5. Proof and regression prevention
- **Proof:** All 214 tests pass successfully when running `python3 -m pytest -q`.
- **Potential remaining break case:** If future test cases introduce custom non-integer currency representations (like floats or decimals instead of paise integers), type guards would need extension to handle Decimal types safely.

## 6. Unresolved challenge or next step
No major blockers remain for the core reward service logic. As a next step, I would investigate adding robust asynchronous logging and database transaction atomicity layers if scaling this service for high-concurrency production environments.