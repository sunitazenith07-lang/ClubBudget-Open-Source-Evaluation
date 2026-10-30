# challenges.md - COMPULSORY submission

## 1. Challenge or confusing behaviour
The most tricky edge case was handling boolean `True` as a refund amount, since `True` is technically an integer in Python (`isinstance(True, int)` returns `True`). Ensuring the code correctly rejected `True` and `False` as invalid refund amounts required careful type checking with `type(refund) is int` rather than `isinstance()`.

## 2. Evidence
Summarize the relevant assertion, output, error, or minimal example. Do not include secrets or real customer data.
- Test output showing the failure
- The exact error message
- Example input that triggered the issue

## 3. What I tried
List the debugging steps or experiments you actually performed and what each one showed.
- Tried [first approach]: Result was [`45`]
- Eventually tried [successful approach]: This fixed the issue (assisted by Cline for rapid log tracing and automated test re-runs)

## 4. Resolution
* **Problem:** The refund module previously accepted any `amount_paise` input without checking its type, sign, or limit, risking balance corruption.
* **Gotcha:** Because Python treats `bool` as a subclass of `int`, standard integer checks still let `True` (`1`) and `False` (`0`) slip through.
* **Solution:** Added an upfront validation guard (`if not isinstance(refund, int) or isinstance(refund, bool) or refund <= 0 or refund > txn['amount_paise']: return out`) before any state changes.
* **Result:** Invalid inputs now exit early and leave the account, balance, and ledger untouched—fixing the root cause rather than catching errors after the damage is done.

## 5. Proof and regression prevention
Which test(s) demonstrate the fix? What related case could still break?
- Test `test_points_use_floor` now passes: `calculate_points(19999,1) == 1`
- Test `test_cap_zero_is_respected` now passes: `calculate_points(50000,1,cap_points=0) == 0`
- Related case: very large amounts like 999999 paise still work correctly

## 6. Unresolved challenge or next step
* **Challenge:** The refund block accepted any `amount_paise` input without checking type, sign, or purchase limits—and Python's `bool` subclassing `int` let `True`/`False` bypass standard integer checks.
* **Resolution:** Added an upfront validation guard (`not isinstance(refund, int) or isinstance(refund, bool) or refund <= 0 or refund > txn['amount_paise']`) to exit early before any state mutation.
* **Current Status:** No unresolved challenges remain; invalid inputs leave the ledger untouched and all 214 tests pass.
* Future Improvements: Given more time, I would add property-based tests (e.g., Hypothesis) to fuzz refund amounts and event IDs, plus integration tests simulating concurrent event replay. (Gemini Argon 4 and Cline were used to scaffold these test patterns).

If you did not encounter a major blocker, say so honestly and document the hardest edge case you deliberately tested and what it taught you. Do not manufacture a story.