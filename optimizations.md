# optimizations.md - Required submission

I didn't add any speed optimizations. My changes were about getting the right answers and making the code easier to read. The full test suite takes about 0.6 s (311 tests, most of that is the random stress tests), so speed wasn't a problem for this task. I did measure how the code behaves with a lot of events, though (section 4).

## 1. Baseline and objective
- What needed improvement: first correctness (67 tests failing), then readability. The starter code crammed each function onto a few long lines joined with `;`, which made the refund bug hard to spot.
- Evidence: all the failures came from wrong rounding, missing input checks and no duplicate check. None were about speed.

## 2. Options considered
| Option | Why it helps | Risk | Decision |
|---|---|---|---|
| Use `//` (whole-number division) instead of `round(a / 10000)` | Exact answers, no decimal errors | None | **Done** |
| One `_is_int` helper for checking numbers | Same check everywhere, and booleans are rejected in one place | One extra small function | **Done** |
| Work out refund points from the total refunded so far | No leftover points from rounding | Needs `refunded_paise` stored per transaction, which the model already has | **Done** |
| Keep `processed_event_ids` as a `list` | Matches the existing account shape and tests (`== ['E1']`) | Searching a list gets slower as it grows | **Kept** |
| Change it to a `set` | Much faster lookup | Breaks what the tests compare against, and loses the order | Not done |
| Keep a hidden `set` next to the list | Fast lookup, list stays the same | Two copies of the same data that could get out of sync | Not done |
| Stop using `deepcopy` for every event | Less copying | The tests require the original account to stay unchanged, and copying by hand is easy to get wrong | Not done |

## 3. Changes implemented
- Change and reason:
  - whole-number maths for points
  - the `_is_int` and `_is_hashable` helpers
  - returning early for rejected events, so each rule is one line you can read
  - working out refund points from the running total
  - a named constant `PAISE_PER_100_RUPEES` instead of a bare `10000`
  - a `_ledger_entry` helper so every ledger line has the same fields
- Tests that protect correctness: all 214 original tests, plus the new ones in `tests/test_regressions.py` and `tests/test_threshold_config.py` and `tests/test_stress.py` (311 total).
- Measurement method and result: I didn't do any speed work, so I'm not claiming a speed improvement.

## 4. Trade-offs
- **Readability vs. shorter code:** `service.py` went from 37 lines to around 110, but each rule is now on its own line, so it's easy to point at in a walkthrough.
- **Correctness vs. speed:** every event copies the whole account (`deepcopy`) and searches the list of processed IDs. Both get slower as the account history grows. I timed it by replaying lots of purchases into one account:

  | Events | Time |
  |---|---|
  | 1,000 | about 0.7 s |
  | 2,000 | about 2.8 s |
  | 4,000 | about 11.2 s |

  Doubling the events makes it about 4× slower. That's fine for the 264-event dataset, but it wouldn't work for a real account with years of history.
- **Strict vs. forgiving input:** rejecting strings like `"100000"` is safer for money, but less forgiving if another system sends numbers as text.

## 5. Further improvements
- If accounts get big: use a set (or a database with a unique ID) for processed events, and stop copying the whole history each time. Then time it again with 10k and 100k events, and re-run all the tests.
- ~~Make the repeat threshold configurable~~. Done as the stretch item: `repeat_threshold_from_config()` and `python -m main --threshold N`.
- Use dataclasses instead of plain dicts, so a typo in a field name gives an error instead of silently doing nothing.
