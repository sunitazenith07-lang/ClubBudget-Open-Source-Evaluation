# AI-Use Declaration

## 1. Tools / Models Used
- **Tool / Model:** Gemini
- **Displayed credits / tokens:** Not available

## 2. Why AI Was Used
- Used to help understand the problem statement requirements, trace why the initial pytest run had 94 failing tests, understand Python edge cases (such as `type(x) is not int` vs `isinstance` for booleans), and organize notes for the code walkthrough.

## 3. What Was Independently Verified and Tested
- Ran `python -m pytest -q` and `python -m main` before and after editing `service.py`.
- Checked each of the 4 main bug fixes in `service.py`:
  1. Floor division `(amount_paise // 10000)` and `(base * (100 + bonus_percent)) // 100`, plus `if cap_points is not None:` so `cap_points=0` returns `0`.
  2. Checking `if event_id in out['processed_event_ids']: return out` so duplicate events do not run twice.
  3. Validating refund amounts (`type(refund) is not int or refund <= 0` and `txn['refunded_paise'] + refund > txn['amount_paise']`).
  4. Using `len(ids) > threshold` in `flag_repeat_transactions` and skipping invalid rows.
- Confirmed that all `219` tests pass (`0 failed`).

## 4. Suggestion Accepted, Modified, or Rejected
- **Suggestion Modified / Rejected:** Rejected adding extra helper functions and changing `processed_event_ids` to a `set`, and instead used simple `type(x) is not int` checks and kept `processed_event_ids` as a `list` so the code stays easy to read, explain, and passes all acceptance tests.