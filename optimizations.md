# Optimizations

## 1. Baseline and objective
The primary objective was correctness and safe handling, not throughput. The untouched suite reported **67 failures**; the dataset contains 180 repeat records and 264 reward events. No timing target was supplied.

## 2. Options considered
- Keep floating-point conversion and adjust rounding: rejected because the specification requires exact integer floor behavior.
- Store processed IDs in a set: it would make membership checks faster, but would change the existing account data shape and its tested output. Kept the list for compatibility.
- Add a database or event-processing framework: rejected because this is an offline, in-memory exercise and the extra infrastructure would obscure the required behavior.

## 3. Changes implemented
- Replaced float-based point calculation with integer division and multiplication. This removes rounding ambiguity; the final suite verifies the boundary matrix and reports **219 passed**.
- Used a dictionary keyed by `(account_id, date, amount_paise)` to group repeat candidates in one traversal. This is straightforward for the supplied data size; no speedup is claimed because no benchmark was run.
- Added validation before event-state mutation, avoiding invalid refund arithmetic and duplicate processing.

## 4. Trade-offs
Keeping `processed_event_ids` as a list preserves the starter’s public state format but makes membership checks linear in the number of processed events. Strict validation adds branches but prevents malformed values from corrupting account state. The dataset is small and the acceptance target is correctness; no timing or memory comparison was measured.

## 5. Further improvements
For production-scale histories, persist events and account updates transactionally, enforce a unique event-ID constraint, and use an indexed/set-backed idempotency store. Measure throughput and memory against representative workloads before choosing that design. Typed models and explicit result types could also replace loosely shaped dictionaries, but would require a broader API migration.