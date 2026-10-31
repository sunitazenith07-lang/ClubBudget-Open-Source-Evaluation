# Approach and implementation decisions

## Evidence and provenance
These notes were prepared with Codex assistance on 2026-10-31 from the four existing commits and verification runs. They do not reconstruct the author's private development history. The original pre-edit test run was not supplied. The starter result below was reproduced afterward from commit `2bc08df` in an isolated directory.

## Baseline
Python 3.12.14, pytest 9.2.0. Reconstructed starter: `python -m pytest -q` -> **67 failed, 147 passed**. Starter demo: points 28, repeat warnings []. Current demo: points 27, repeat warnings [].

## Codebase and flow
`models.new_account` creates balance, transaction, processed-ID and ledger state. `fixtures.py` supplies the offline demo; `main.py` calls points and repeat grouping. `service.calculate_points` validates rules, floors the purchase amount, applies the bonus and then the cap. `apply_reward_event` copies the account, rejects missing/replayed IDs and dispatches captures/refunds. Accepted events update balance, transaction totals, ledger and processed IDs together. Repeat alerts group valid records by account/date/amount. `data/records.json` is additional synthetic investigation material, not the demo input or an automatically executed test suite.

## Four implementation steps
| Commit | Defect and evidence | Implemented correction |
|---|---|---|
| `268e12d` | 19,999 paise rounded to 2 rather than 1; zero cap ignored | Integer floor division; explicit cap validation |
| `87154ca` | Replayed purchases failed idempotency tests | Check event IDs before updates; record IDs after acceptance; validate captures |
| `07912ad` | Invalid/excess refunds changed refund totals | Positive integer validation and cumulative amount bounds before mutation |
| `bfb1368` | Repeat grouping lacked safe input handling and deterministic ordering | Validate rows/threshold, group by complete key, sort output; add five regressions |

The starter already used a strict `count > threshold` comparison; the fourth commit preserves this contract rather than introducing it.

## Decisions and alternatives
Integer arithmetic follows the contract without floating-point rounding. Cumulative refund rounding avoids losing reversal fractions across installments. Rejected refunds leave state unchanged instead of being silently truncated. Deep copying preserves caller state; an in-place implementation would be cheaper but would change the API contract. These are review observations, not claims about alternatives personally tried during the original implementation.

## Verification
Current suite: **219 passed**, no failures/errors/skips. Five regression functions cover refund replay, cumulative excess refunds, duplicate transaction IDs, missing IDs, and invalid rules. An original reversed-points assertion removed in the fourth commit was restored during documentation preparation. Workflows and acceptance-matrix tests were unchanged. See TESTING.md for commands and known limits.
