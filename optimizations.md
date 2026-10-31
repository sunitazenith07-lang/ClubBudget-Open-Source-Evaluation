# Optimizations and trade-offs

## Objective and evidence
The four commits primarily improve correctness, not measured performance. The reconstructed starter had 67 failures; the current suite has 219 passes. These counts establish test outcomes, not a speedup.

## Implemented choices
- Integer floor arithmetic avoids float conversion and matches paise/bonus rounding. Protected by the floor and bonus/cap matrices.
- Event-ID validation exits before transaction updates on replay. Membership still scans a list; no constant-time lookup claim is made.
- Repeat records are collected into a dictionary in one pass rather than compared pairwise. With n valid rows and g groups, expected grouping cost is O(n), output sorting O(g log g), and storage O(n). Sorting makes review output deterministic.
- Refund bounds are checked before mutation, retaining cumulative rounding and preventing invalid bookkeeping.

## Alternatives and trade-offs
These alternatives were considered during this documentation review, not measured in the original development. A set could accelerate processed-ID lookup, but persistent list ordering/serialization and compatibility need care. Deep copying protects input immutability but copies growing history on every event; copying only changed structures would reduce work at the cost of aliasing risks. Sorting repeat groups adds cost but gives stable output. No benchmark supports a numerical performance claim.

## Next improvements
Benchmark long event histories before replacing list lookup or deep copying. Add explicit identifier/schema validation with malformed-input regressions. If persistence is introduced, make ledger and idempotency updates atomic and enforce unique event IDs. Keep any such work separate from this focused submission.
