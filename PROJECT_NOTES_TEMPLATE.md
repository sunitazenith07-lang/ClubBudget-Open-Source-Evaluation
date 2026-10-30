# Project Notes — RewardBook

## Requirements completed

1. **Integer Floor Arithmetic Points Calculation:**
   - Implemented `base_points = (amount_paise // 10000) * points_per_100_rupees`.
   - Implemented `bonus_points = (base_points * (100 + bonus_percent)) // 100`.
   - Applied optional `cap_points` with strict handling for `cap_points = 0` yielding 0 points.
   - Safely excluded non-integers, floats, strings, booleans, and negative inputs.

2. **Idempotency & Event Processing:**
   - Enforced single-execution guarantee per `event_id`: replaying purchase or refund events returns account state unchanged.
   - Prevented replaying duplicate captures under existing `transaction_id`.
   - Ignored non-captured purchase events (`purchase_declined`, `purchase_pending`, `unknown_event`) without awarding points or mutating ledger.

3. **Proportional Refund Reversal & Balance Integrity:**
   - Computed cumulative proportional reversal: `should_reverse = (awarded_points * new_refunded) // amount_paise`.
   - Guaranteed cumulative refunded amount cannot exceed original purchase amount (`refunded_paise + refund <= amount_paise`).
   - Enforced non-negativity floor on points balance: reversal delta cannot reduce `points_balance` below zero.

4. **Auditable Ledger:**
   - Appended a ledger entry for every accepted purchase (`points_delta > 0`) and refund (`points_delta < 0`).
   - Verified ledger delta sum exactly matches `points_balance` across all synthetic records.

5. **Repeat Transaction Detection:**
   - Grouped transactions by composite tuple `(account_id, date, amount_paise)`.
   - Flagged groups where `len(ids) > threshold`, defaulting safely to `threshold = 2` when missing or `None`.
   - Ensured deterministic output ordering sorted by group key.

6. **Boundary & Malformed Input Hardening:**
   - Neutralized the `setdefault()` null-trap for corrupted account states.
   - Handled `bonus_percent = None` defaulting to 0% bonus.
   - Rejected cross-account event pollution where `event['account_id'] != account['account_id']`.

## Files changed

- [service.py](file:///Users/vee/Desktop/opensource/RewardBook-Open-Source-Evaluation-fork/service.py): Rewrote `calculate_points`, `apply_reward_event`, and `flag_repeat_transactions` with complete type guards, boundary checks, and cumulative reversal logic.
- [models.py](file:///Users/vee/Desktop/opensource/RewardBook-Open-Source-Evaluation-fork/models.py): Cleaned up account factory with string coercion and container initialization.
- [fixtures.py](file:///Users/vee/Desktop/opensource/RewardBook-Open-Source-Evaluation-fork/fixtures.py): Formatted offline demo fixtures according to PEP 8 standards.
- [main.py](file:///Users/vee/Desktop/opensource/RewardBook-Open-Source-Evaluation-fork/main.py): Structured offline entrypoint running points example and repeat transaction warning checks.
- [tests/test_regression.py](file:///Users/vee/Desktop/opensource/RewardBook-Open-Source-Evaluation-fork/tests/test_regression.py): Created 15 regression test cases covering null-trap protection, boundary rounding, over-refunds, and idempotency.
- [TESTING.md](file:///Users/vee/Desktop/opensource/RewardBook-Open-Source-Evaluation-fork/TESTING.md): Recorded environment details, 8 documented edge cases, and regression summary.
- [challenges.md](file:///Users/vee/Desktop/opensource/RewardBook-Open-Source-Evaluation-fork/challenges.md): Detailed the null-trap on corrupted accounts, boolean subclassing, and cap falsiness.
- [approach.md](file:///Users/vee/Desktop/opensource/RewardBook-Open-Source-Evaluation-fork/approach.md): Documented baseline, code flow investigation, and implementation decisions.
- [optimizations.md](file:///Users/vee/Desktop/opensource/RewardBook-Open-Source-Evaluation-fork/optimizations.md): Documented memory, immutability, and performance trade-offs.
- [REWARD_RULE_NOTES.md](file:///Users/vee/Desktop/opensource/RewardBook-Open-Source-Evaluation-fork/REWARD_RULE_NOTES.md): Documented worked calculations, partial refund flow, and core assumptions.

## Decisions and assumptions

- **Pure Integer Arithmetic:** All calculations avoid floating-point math to prevent IEEE-754 precision inaccuracies in currency conversion and points calculations.
- **Cumulative Refund Proportionality:** Calculating reversals using cumulative refunded paise rather than incremental partial ratios eliminates rounding drift across multi-stage refunds.
- **Caller Immutability:** Maintained `deepcopy()` on input accounts to ensure caller references are never mutated in place.
- **Fail-Safe Discarding:** Malformed events, missing identifiers, unknown transaction types, or invalid amounts are discarded early without corrupting account balances or polluting the ledger.

## Tests and results

- **Test Command:** `python3 -m pytest -v`
- **Baseline Result:** 67 failed, 147 passed (214 tests total).
- **Final Result:** **229 passed, 0 failed in 0.14s**.
  - `tests/test_contract.py`: 12 passed
  - `tests/test_acceptance_matrix.py`: 142 passed
  - `tests/test_regression.py`: 15 passed
- **Offline Demo Execution:** `python3 -m main`
  - `Points example: 27` (corrected from starter's erroneous 28)
  - `Repeat warnings: []` (matches strict `threshold = 2` boundary)
- **Dataset Stress Test:** All 264 reward events across 40 accounts in `data/records.json` simulated across 8 rule cases with zero assertion errors and 100% ledger balance consistency.

## Limitations and next steps

- **Concurrency:** Current implementation is in-memory and synchronous. In a production microservice with concurrent webhooks, database row-level locking (`SELECT ... FOR UPDATE`) or an append-only event-sourcing ledger would be required to prevent race conditions.
- **Sliding Date Windows:** Repeat transaction detection currently groups by exact calendar date strings (`date`). An enhancement would support rolling time windows (e.g. 24 hours across calendar day boundaries).
