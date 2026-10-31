# Testing evidence

## Environment and commands
Verified with Codex assistance on 2026-10-31: Windows, Python **3.12.14**, pytest **9.2.0**. Python was invoked by its bundled absolute executable path because the default launcher was unavailable.

```powershell
python -m pip install --target .venv/test-deps -r requirements-dev.txt
$env:PYTHONPATH=(Resolve-Path .venv/test-deps).Path
python -m pytest -q
python -m main
```

Here `python` represents that executable. Current run: **219 passed; 0 failed, 0 errors, 0 skipped**. Demo: `Points example: 27`, `Repeat warnings: []`.

The original development baseline was not supplied. An isolated archive of `2bc08df`, tested after the four commits, produced **67 failed, 147 passed** (214 total); its demo returned 28 points. This is reconstructed evidence, not a claimed original run. The larger synthetic JSON dataset was inspected for schema/context, not exhaustively replayed by a separate harness.

## Edge-case evidence
All named tests below ran in the passing current suite. Test names are in `tests/test_contract.py` unless noted.

| Input | Expected | Actual | Evidence |
|---|---|---|---|
| 19,999 paise, rate 1 | 1 point | 1; pass | `test_points_use_floor` |
| 50,000 paise, rate 1, cap 0 | 0 points | 0; pass | `test_cap_zero_is_respected` |
| 50,000 paise, rate 2, bonus 50%, cap 6 | 6 points | 6; pass | `test_bonus_then_cap` |
| Same purchase E1 replayed | Balance 2, one processed ID | Matches; pass | `test_purchase_event_once` |
| Refund 50,000 of 100,000 paise | Balance 5, reversed points 5 | Matches; pass | `test_partial_refund_reverses_proportionally` |
| Refund -1 or 150,000 of 100,000 | Balance 10, refunded amount 0 | Matches; pass | `test_invalid_or_excess_refund_ignored` |
| Refund R1 replayed | Balance 5, processed IDs E1/R1 | Matches; pass | `test_refund_event_once` |
| Refund 60,000 then 50,000 of 100,000 | Second rejected, balance 4 | Matches; pass | `test_multiple_partial_refunds_cannot_exceed_purchase` |
| New event ID for existing transaction | Balance 5, one ledger entry | Matches; pass | `test_duplicate_transaction_id_not_awarded_twice` |
| Missing identifiers / empty event | Balance 0 | Matches; pass | `test_missing_ids_and_empty_event_ignored` |
| Boolean amount / negative rule | 0 points | 0; pass | `test_boolean_and_negative_rules_return_zero` |
| Counts equal to / above threshold | No alert / one alert | Pass for 10 thresholds | `tests/test_acceptance_matrix.py::test_repeat_alert_threshold_boundaries` |

## Regression coverage and test preservation
The fourth commit adds five regression functions: refund replay, cumulative refund bounds, duplicate transaction IDs, missing IDs, and invalid rules. During this review the original partial-refund reversed-points assertion was restored. No test was deleted/skipped and CI was not modified.

## Limitations
GitHub CI is separate from the local result; its latest state must be checked on the PR. No coverage percentage or performance result was measured. Malformed account schemas/unhashable identifiers, concurrent writes and persistence remain outside current guarantees.
