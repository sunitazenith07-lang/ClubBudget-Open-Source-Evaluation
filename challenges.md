# challenges.md - COMPULSORY submission

I am a first-year student who recently finished learning the basics of Python. I did not face one single blocker for days. The challenges below are the ones I actually worked through, with evidence. I have not invented a struggle to fill this page.

## 1. Challenge or confusing behaviour
What specific calculation, event, test failure, refund rule, ledger entry, or repeat-alert case was difficult to understand?
1. `True` as a refund amount passed a simple `isinstance(refund, int)` check.
2. I first thought a repeat alert should appear when the count reaches the threshold. That was wrong.
3. I first thought checking the transaction id was enough for idempotency. It was not: the event id also matters.
4. Two partial refunds together were confusing: the second refund must not be calculated from its own amount alone.
5. Probing with `None` inputs crashed functions that already passed all visible tests.

## 2. Evidence
Summarize the relevant assertion, output, error, or minimal example. Do not include secrets or real customer data.
- Bool: `test_invalid_or_excess_refund_does_not_change_account[True]` — `isinstance(True, int)` returns `True` and `True > 0` is `True`, so `True` was treated like 1 and changed `refunded_paise` from 0 to 1.
- Threshold: `test_repeat_alert_threshold_boundaries` creates exactly threshold rows and expects `[]`, then adds one more row and expects one alert. The rule is therefore `count > threshold`, not `>=`. With threshold 2, the demo's two identical rows give no alert, which is why `python -m main` prints `Repeat warnings: []`.
- Event vs transaction: on the starter, replaying a purchase gave `processed_event_ids == ['E1', 'E1']`, expected `['E1']` (`test_purchase_event_once`).
- Cumulative refund: purchase 100000 → 10 points. Refund 30000 reverses 3 (balance 7). A second refund of 70000 must reverse the remaining 7, not another 7 calculated in a way that double-counts, and the total must never exceed 10.
- None crash: `apply_reward_event(account, None, rules)` raised `AttributeError: 'NoneType' object has no attribute 'get'`, and `flag_repeat_transactions(None)` raised `TypeError: 'NoneType' object is not iterable`, even though all visible tests passed at that time.

## 3. What I tried
List the debugging steps or experiments you actually performed and what each one showed.
- I tested `isinstance(True, int)` directly in the terminal. It returned `True`, which explained why my original validation was not enough.
- I traced the demo by hand: 259900 paise → `259900 // 10000 = 25` base points → `25 * 110 // 100 = 27` with a 10% bonus. The starter gave 28 because it used `round(25.99) = 26` first.
- I read the related tests before changing the threshold logic: `test_different_accounts_not_grouped`, `test_repeat_alert_respects_threshold` (counts 1 to 20), and `test_repeat_alerts_do_not_mix_distinct_keys`.
- For refunds, I worked the cumulative case on paper before coding it: total reversed must be `awarded * cumulative_refunded // purchase_amount`, and each event subtracts only `total_reversed - already_reversed`.
- For the None crashes, I probed beyond the visible tests with a small script: event `None`, rules `None` and `[]`, account `None`, transaction list `None`, and threshold `'x'`. Those probes became the final tests, not just notes.

## 4. Resolution
What was the root cause? What did you change, and why did it fix the cause rather than hide the symptom?
- Bool: I created a helper, `is_valid_int(value) = isinstance(value, int) and not isinstance(value, bool)`, and I use it everywhere a number is checked, together with `>= 0`. Now `True` and `False` are never treated as valid integer inputs.
- Floor and cap: base points use integer `//`, and the cap check is `if cap_points is not None:`, so cap 0 means 0 points and `None` means no cap. Bonus is applied before the cap.
- Event id: I added an early return if `event_id is None` or if the id is already in `processed_event_ids`, and I kept the transaction-id check as well. Missing ids are never recorded, otherwise every missing-id event would collide on `None`.
- Cumulative refund: reversal is computed from cumulative `refunded_paise`, capped with `min(..., awarded_points)`, and only the incremental delta is subtracted. A refund is accepted only if it is a valid int, not negative, and cumulative refunds never exceed the purchase amount. The balance is also clamped at zero.
- Threshold: I kept `len(ids) > threshold` and added skipping for malformed rows (not a dict, or any key field `None`). I did not change the rule for amounts of 0 or -1, because they are not `None` — they are still grouped, and that is a deliberate choice.
- None inputs: a non-dict event or rules returns the account unchanged, a non-dict account returns a blank safe account, a `None` transaction list returns `[]`, and an unusable threshold returns `[]` instead of crashing.

## 5. Proof and regression prevention
Which test(s) demonstrate the fix? What related case could still break?
- Bool and invalid refunds: all 15 invalid refund cases in `test_invalid_or_excess_refund_does_not_change_account` now pass, including `True`, `False`, `None`, `"100"`, `1.5`, `[]` and `{}`.
- Repeat alerts: `test_repeat_group`, `test_different_accounts_not_grouped`, `test_repeat_alert_respects_threshold`, `test_repeat_alert_threshold_boundaries`, `test_repeat_alerts_do_not_mix_distinct_keys`, and `test_repeat_alert_threshold_input_is_handled` all pass.
- Refunds and ledger: `test_partial_refund_reverses_proportionally`, `test_refund_event_replay_once`, `test_multiple_partial_refunds_exceeding_purchase_ignored`, `test_cumulative_refund_and_ledger_audit_trail` (ledger `[10, -3, -7]`, final balance 0), and the final tests for missing identifiers and `None` inputs all pass.
- Full suite on this version: **223 passed, 0 failed**.
- What could still break, honestly: a hidden test that expects a corrected payload to be accepted under a previously used event id (see §6), or that expects a float amount to be coerced instead of rejected. Both are judgement calls I made and documented in `approach.md` §4, not cases I failed to notice.

## 6. Unresolved challenge or next step
State remaining limitations and how you would investigate them next.
The one behaviour I deliberately left as-is is this: a well-formed but business-invalid event still consumes its event id. For example, a declined event with id `E1` blocks a later purchase with the same id `E1` (balance stays 0), and an invalid refund with id `E2` blocks a later valid refund with id `E2`. That is the safe reading of "process each event_id once", and it protects against true replays. Its cost is operational: a genuinely corrected retry must use a new event id, because the system does not distinguish "rejected, retry allowed" from "already processed". If I had more time, I would ask the problem setter whether rejected events should be kept in a separate list, so a corrected retry could be accepted while true replays stay blocked, and I would add a test for that distinction before changing the code.
Two other known limitations, not blockers: repeat grouping counts the same transaction id twice if the input list itself repeats it (the input is assumed to contain distinct ids), and two purchase events with different event ids but the same transaction id are silently ignored — the second event does not overwrite the first record. In future I would add a warning or flag for that case so it can be reviewed instead of being silently ignored.
