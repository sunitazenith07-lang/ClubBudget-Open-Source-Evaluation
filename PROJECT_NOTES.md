# Project Notes

ok so these are the notes. most of this is already in the other files but whatever, here it is in one place.

## Requirements completed

all 8. the list:

1. points round **down** now. 19999 paise = 1 point, not 2. the old code used `round()`, which was just wrong
2. bonus gets added, then the cap goes on last. a cap of 0 actually counts now (before, `if cap_points:` thought 0 meant "no cap" lol)
3. the same event can't count twice. it checks `processed_event_ids` now. before it saved the ids and then just... never looked at them
4. events with no `event_id` / `transaction_id`, or a weird amount (`True`, `"100"`, `1.5`, 0, negative), get ignored
5. refunds can't go over the purchase amount, even split across a few refunds
6. partial refunds take back points from the **total** refunded so far. that way a full refund always takes everything back and doesn't leave 1 random point behind
7. the balance never goes below 0, and every ledger line has `transaction_id`, `amount_paise` and `balance_after`, so you can see what happened
8. repeat alerts: group by account + date + amount, alert if there are **more than** the threshold, skip junk rows, same order every time, marked `needs_review`. they never block anything

also did an "ambiguity fix" at the end. two alert things weren't wrong exactly but were weird: a junk threshold like `None` became 1 (so more alerts, not fewer), and the same transaction sent 3 times counted as a repeat of itself. now junk falls back to 2 and each id counts once.

also did the stretch thing. the threshold is configurable now: `python -m main --threshold N`, or `repeat_alert_threshold` in the config. default is still 2.

## Files changed

- `service.py`: basically all the actual fixes are here
- `main.py`: added the `--threshold` option. that's it
- `tests/test_regressions.py`: new, 56 tests for the fixes
- `tests/test_threshold_config.py`: new, 15 tests for the threshold thing
- `tests/test_stress.py`: new, 34 tests that throw thousands of random inputs at the code
- `approach.md`, `challenges.md`, `optimizations.md`, `TESTING.md`, `REWARD_RULE_NOTES.md`: the required docs
- `ARCHITECTURE.md`, `PROJECT_NOTES.md` (this one), `PR_DESCRIPTION.md`, `AI_USAGE.md`: extra docs

didn't touch any of the original tests or the CI file. not allowed to, and didn't need to.

## Decisions and assumptions

- money is always whole paise. no floats anywhere, because floats are bad at money
- bad rules (like a negative bonus) give 0 points. they don't get "fixed" automatically
- rejected events don't get marked as processed, so you can resend a fixed version
- amount-0 transactions don't count for alerts. not real purchases. this gives 48 alert groups on the dataset instead of 60. honestly not sure this is what they want, but it made sense
- `"100000"` as a string gets rejected, not converted. safer i guess
- a threshold below 1 just counts as 1. junk like `None` or `"2"` uses the default 2 instead
- if the same transaction id shows up twice in a group it only counts once. a duplicated row isn't a repeat payment
- if an ID is a list or dict (it happens in bad json), the event gets skipped instead of crashing. found this one with the stress tests

## Tests and results

- starter code: `67 failed, 147 passed`
- after fixing stuff: `249 passed`
- after the threshold thing: `264 passed`
- after the stress-test fixes: `277 passed`
- after adding the stress tests: `311 passed` locally (python 3.14.7)
- after making the alert function return `[]` for non-list input (it crashed on a plain number): `314 passed`
- after fixing junk thresholds (they now fall back to 2) and not counting the same transaction id twice: `319 passed`
- CI on github (python 3.11, before the last two fixes): `314 passed, 0 failed`. run: https://github.com/madhavmongaa/RewardBook-Open-Source-Evaluation/actions/runs/41121388655
- `python -m main` prints `Points example: 27` (the old one said 28, which was wrong)

edge cases are in `TESTING.md` if you want them. there are 13.

## Limitations and next steps

- it gets slow with lots of events, because every event copies the whole account. 1k events ≈ 0.7s, 4k ≈ 11s. fine for this dataset, not fine for real life. fix: use a set or a database for the event ids and stop copying everything
- if someone already spent their points and then gets a refund, it only takes back what's left. the rest just kind of disappears. would need some "points owed" thing
- string amounts get rejected, so if some other system sends numbers as text, people get 0 points
- amount-0 alerts: someone should decide if those count. it's a one-character change if they do
- could swap the dicts for dataclasses so typos actually throw errors. didn't bother
