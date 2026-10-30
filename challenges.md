# challenges.md

## 1. Challenge or confusing behaviour
The most confusing behavior was the distinction between a repeated event and
a repeated transaction. A duplicate purchase event must not award points or
append history twice, while a new refund event for the same transaction can
still be valid.

## 2. Evidence
The initial test run reported `67 failed, 147 passed in 0.35s`. A focused
replay check produced duplicate processed IDs:

```text
purchase replay: 2 2 ['P1', 'P1'] 1
```

Invalid refund checks also showed:

```text
refund -1      => refunded_paise=-1, balance=11
refund 150000  => refunded_paise=150000, balance=-5
refund None    => TypeError
```

## 3. What I tried
1. Read the calculation, purchase, refund, ledger, and replay assertions in
   both test files.
2. Ran the full suite to identify the failing categories.
3. Ran focused Python examples for `19999` paise, a zero cap, duplicate
   purchases, and invalid refunds.
4. Compared account balance, processed event IDs, transaction refund totals,
   and ledger length before and after each event.
5. Reran the full suite after the implementation changes.

## 4. Resolution
The root causes were nearest-unit rounding, a truthiness check that
discarded a zero cap, missing input validation, and no event-ID guard before
state mutation. I changed the calculation and event-processing boundaries
themselves: integer floor division, explicit `None` handling, validation
before mutation, and an early duplicate-event return. This fixes the state
transitions rather than weakening test expectations.

## 5. Proof and regression prevention
The fix is demonstrated by `test_points_use_floor`,
`test_cap_zero_is_respected`, `test_purchase_event_replay_is_idempotent`,
`test_partial_refund_reverses_proportionally`, and
`test_invalid_or_excess_refund_does_not_change_account`. The full suite
passes with `214 passed in 0.08s`.

A related case that could still break in production is concurrent delivery
of the same event to separate processes, because the current account state
is held only in memory.

## 6. Unresolved challenge or next step
No local test failure remains. The next step would be a persistence-backed
uniqueness constraint for event IDs and an integration test that delivers
the same event concurrently.

I did not encounter a blocking environment issue. The deliberate replay and
refund tests showed that preventing duplicate awards is not sufficient:
invalid events must also be prevented from mutating transaction state.