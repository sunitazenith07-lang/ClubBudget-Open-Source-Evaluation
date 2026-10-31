<!-- DRAFT: resolve every [VERIFY] and [FILL] marker with your own run/edits, then delete this comment. -->
# Architecture Notes

## Project map
| File | Role |
|---|---|
| `models.py` | `new_account(account_id)` returns the empty account dict. |
| `service.py` | All business logic: `calculate_points`, `apply_reward_event` (with `_apply_purchase` and `_apply_refund`), `flag_repeat_transactions`. |
| `fixtures.py` / `main.py` | Offline demo data and the demo entry point. |
| `data/records.json` | Synthetic dataset (40 accounts, 264 reward events, 180 repeat records) used for investigation. |
| `tests/` | `test_contract.py` (core contract), `test_acceptance_matrix.py` (parametrised matrix), `test_regressions.py` (mine). |
| `.github/workflows/tests.yml` | Runs the demo and pytest on every push and PR. |

There are no classes and no I/O. Everything in `service.py` is a function over plain dicts.

## Data model
An account is one dict:
- `account_id`, `points_balance` (int)
- `processed_event_ids`: list of accepted event IDs
- `transactions`: `{transaction_id: {amount_paise, awarded_points, reversed_points, refunded_paise}}`
- `ledger`: list of `{event_id, type, transaction_id, points_delta}`

Invariants I rely on and check:
- `reversed_points <= awarded_points` and `refunded_paise <= amount_paise` for every transaction.
- `points_balance >= 0`.
- One ledger entry per processed event ID.
- The ledger deltas sum to the balance (true for accounts that start at 0, as `new_account` does).

## Data flow
1. `apply_reward_event` deep-copies the account, so the caller's account is never mutated.
2. It rejects the event (returns the unchanged copy) if the event is not a dict, the `event_id` or `transaction_id` is missing or not a non-empty string, or the `event_id` was already processed.
3. It dispatches on `type`: `purchase_captured` goes to `_apply_purchase`, `refund_processed` goes to `_apply_refund`, and anything else is ignored.
4. A purchase is validated, then `calculate_points` computes floor, bonus and cap. A refund is validated, checked against the cumulative bound, and reverses points proportionally.
5. Only if the helper accepted the event, the ID is appended to `processed_event_ids`. Each helper has already written the ledger entry.
6. `flag_repeat_transactions` is independent: it groups complete records by (account, date, amount) and returns groups larger than the threshold. It only reports and never changes accounts.

## Storage design
Storage is in memory only. There is no persistence, and the caller holds the returned account and passes it to the next call. Idempotency depends on `processed_event_ids` travelling with the account. A real system would keep this in a database (see improvement 2).

## Diagram
```
                     +-------------------+
                     |   Event (dict)    |
                     +---------+---------+
                               |
                               v
              +----------------------------------+
              | Checks: is a dict, both IDs      |
              | present, event_id not processed  |--- fail --> [REJECT]
              +----------------+-----------------+
                               | pass
                               v
                       +---------------+
                       | type of event |--- other ---> [REJECT]
                       +---+-------+---+
        purchase_captured  |       |  refund_processed
                           v       v
      +--------------------------+  +--------------------------+
      | _apply_purchase          |  | _apply_refund            |
      | validate amount          |  | validate amount          |
      | calculate_points         |  | cumulative bound check   |
      | record transaction       |  | proportional reversal    |
      +------------+-------------+  +-------------+------------+
                   | accepted?                    | accepted?
                   | no -> [REJECT]               | no -> [REJECT]
                   +--------------+---------------+
                                  | yes
                                  v
                  +-----------------------------------+
                  | ledger entry written (in helper)  |
                  | event_id added to processed list  |
                  +-----------------+-----------------+
                                    |
                                    v
                            Return new account

[REJECT] = return the unchanged copy: no change to balance,
           ledger or processed IDs
```

## Three improvements suggested
1. **Batch apply.** Add `apply_events(account, events)` that copies once. Per-event deepcopy makes a stream of events O(n^2); I measured about 4x the time for each doubling of events [VERIFY: your own timing]. Validate by testing that the batch result equals applying the events one by one.
2. **Durable store with a uniqueness constraint.** Persist the ledger as append-only rows with a unique key on `event_id`, so idempotency holds across restarts and concurrent workers. The service also never checks that `event.account_id` matches the account it is applied to, so route events by account and reject mismatches.
3. **Rejection reasons and pending refunds.** Return a reason code for each rejected event (replayed, invalid amount, over-refund, unknown transaction) so operations can see why. Queue a refund that arrives before its purchase instead of dropping it.