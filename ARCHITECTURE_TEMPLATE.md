# Architecture Notes

## Project map

- `models.py` — factory for the account aggregate (`new_account`).
- `service.py` — pure business logic: `calculate_points`, `apply_reward_event`, `flag_repeat_transactions`, plus the `_is_int` guard.
- `fixtures.py` — sample account, transactions and rules used by the offline demo.
- `main.py` — demo entry point (`python -m main`).
- `tests/` — `test_contract.py` and `test_acceptance_matrix.py` (214 tests total).
- `data/` — expanded synthetic dataset (`records.json`) and schema notes.
- Templates/notes at repo root document approach, challenges, optimizations, testing, reward rules and AI usage.

## Data model

- **Account** (`dict`):
  - `account_id` (`str`)
  - `points_balance` (`int`)
  - `processed_event_ids` (`list[str]`) — idempotency log
  - `transactions` (`dict[transaction_id -> Transaction]`)
  - `ledger` (`list[LedgerEntry]`)
- **Transaction** (`dict`):
  - `amount_paise` (`int`)
  - `awarded_points` (`int`)
  - `reversed_points` (`int`)
  - `refunded_paise` (`int`)
- **Event** (`dict`):
  - `event_id`, `type` (`purchase_captured` | `refund_processed`), `transaction_id`, `amount_paise`
- **Rules** (`dict`):
  - `points_per_100_rupees` (`int`), `bonus_percent` (`int`), `cap_points` (`int | None`)
- **Repeat key**: `(account_id, date, amount_paise)` grouping transaction ids.

## Data flow

1. `calculate_points(amount_paise, points_per_100_rupees, bonus_percent=0, cap_points=None)`:
   - Validate all numeric inputs are non-bool ints; return `0` otherwise.
   - Reject non-positive amounts/rules; a cap of `0` yields `0`.
   - `base = (amount_paise // 10000) * points_per_100_rupees` (floor).
   - `points = base * (100 + bonus_percent) // 100` (floor bonus).
   - Apply `cap_points` last via `min`; clamp with `max(0, points)`.
2. `apply_reward_event(account, event, rules)`:
   - Deep-copy the account so callers are not mutated; ensure default keys.
   - Return unchanged copy for non-dict event/rules (rules coerced to `{}`).
   - Idempotency: if `event_id` already in `processed_event_ids`, return unchanged.
   - `purchase_captured`: calculate points, create transaction record if new, add to balance, append ledger entry.
   - `refund_processed` (only if `transaction_id` exists): validate refund is a positive int and `refunded_paise + refund <= amount_paise`; otherwise ignore. On valid refund, update cumulative refund, compute proportional reversal `awarded * refunded // amount`, apply delta with a non-negative balance floor, record ledger entry.
   - Append `event_id` to `processed_event_ids` for any accepted/ignored event.
3. `flag_repeat_transactions(transactions, threshold=2)`:
   - Guard non-list input and non-int thresholds (coerce or reset to 0).
   - Skip non-dict entries; group by `(account_id, date, amount_paise)`.
   - Emit an alert per group with `len(ids) > threshold`, sorted by key.

## Storage design

- All state is held in in-memory Python dicts/lists; there is no persistence layer.
- `deepcopy` in `apply_reward_event` preserves caller immutability.
- Idempotency relies on `processed_event_ids` (a list); membership checks are O(n).
- Ledger is an append-only list of `{event_id, type, points_delta}` entries for auditability.

## Diagram

```
event ──► apply_reward_event(account, event, rules)
             │
             ├── idempotency check (processed_event_ids)
             ├── purchase_captured ──► calculate_points ──► transaction + balance + ledger
             └── refund_processed ──► validate cumulative refund ──► proportional reversal + ledger
transactions ──► flag_repeat_transactions ──► grouped alerts (account,date,amount)
```

## Three improvements suggested

1. Replace `processed_event_ids` list with a `set` for O(1) idempotency lookups while keeping an ordered list for audit if needed.
2. Introduce schema validation (e.g. dataclasses/Pydantic) for accounts/events/rules to fail fast on malformed payloads instead of silent guards.
3. Add property-based tests for cumulative refund sequences and a persistence/transactional storage layer for the ledger.

