# optimizations.md

## 1. Baseline
I focused on correctness, not speed. I noticed that checking event_id in a list is O(n) and deepcopy runs on every event, but I did not measure either.

## 2. Options considered
- Use a set for processed event ids: faster lookups, but it changes the account format.
- Remove deepcopy: faster, but the input account would be modified.

## 3. Changes implemented
None. No speed claim is made because I did not measure anything.

## 4. Trade-offs
I kept the list and deepcopy because they are simple and keep the caller's account safe.

## 5. Further improvements
Time the code with timeit on a large number of events, and try a set only if it is slow.