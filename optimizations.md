<!-- DRAFT: resolve every [VERIFY] and [FILL] marker with your own run/edits, then delete this comment. -->
# optimizations.md

## 1. Baseline and objective
- Correctness came first, and that was the whole fix. After it, I looked at repeated work, because `apply_reward_event` deep-copies the whole account on every event.
- Evidence: timing 1000, 2000 and 4000 sequential purchase events on one account (script below). Each doubling of events about quadrupled the time. [VERIFY: re-run and paste your numbers; mine were 2.4 s, 10.1 s and 40.8 s.]

```python
import time
from service import apply_reward_event
from models import new_account
for n in (1000, 2000, 4000):
    a = new_account('A'); t = time.perf_counter()
    for i in range(n):
        a = apply_reward_event(a, {'event_id': f'E{i}', 'type': 'purchase_captured',
                                   'transaction_id': f'T{i}', 'amount_paise': 25000},
                               {'points_per_100_rupees': 1})
    print(n, round(time.perf_counter() - t, 3))
```

## 2. Options considered
- **A. Keep the per-event deepcopy (chosen).** No benefit, but the tests require that the input account is not mutated (`test_event_processing_does_not_mutate_input_account`).
- **B. Copy only what changes (shallow copy plus new ledger and ID lists).** Less work per event, but the lists are still O(n) to copy, and nested transaction dicts could leak mutations. Risky for the benefit.
- **C. Add a set for processed-ID lookup.** The list scan is O(n), but the tests compare `processed_event_ids` to a list, so I would need to keep both in sync.
- **D. A batch function `apply_events(account, events)` that copies once.** About O(n) overall, and the existing per-event function stays as the contract. This is my preferred next step.

## 3. Changes implemented
- No performance change. I have not measured any speedup.
- Maintainability changes only: shared `_is_int` validation, `PAISE_PER_100_RUPEES` constant, purchase and refund split into helpers, and early returns instead of nested branches. The full suite (226 tests [VERIFY]) protects behaviour.

## 4. Trade-offs
- Keeping deepcopy costs speed but keeps the function pure and easy to test.
- Rejecting events instead of clamping costs flexibility but keeps the ledger honest.

## 5. Further improvements
- Implement option D, then test that applying events through the batch function gives the same result as applying them one by one, and re-run the timing script above.
- Profile before changing anything. I assume deepcopy dominates, but I have not profiled it.