# Optimizations — RewardBook

## 1. Baseline observations

The initial implementation had several correctness issues identified through the baseline test run.

The baseline result was:

```text
147 passed, 67 failed
```

The main areas requiring improvement were:

- Reward calculation accuracy.
- Handling of zero-valued reward caps.
- Duplicate event processing.
- Refund validation.
- Consistency of transaction and reward records.

## 2. Implemented improvements

### A. Integer-based reward calculation

**Previous approach:** Floating-point division and rounding.

**Improved approach:** Integer floor division.

```python
base = (amount_paise // 10000) * points_per_100_rupees
```

**Benefit:**
- Avoids floating-point rounding errors.
- Produces predictable results at reward boundaries.
- Keeps monetary calculations in integer paise.

### B. Correct cap handling

The implementation checks whether the cap is `None` rather than relying on truthiness.

**Benefit:**
- A zero-point cap is respected.
- Optional caps remain supported.

### C. Duplicate-event protection

An early check against processed event IDs prevents the same event from being applied repeatedly.

**Benefit:**
- Prevents duplicate reward credits and refund reversals.
- Keeps the processed-event list consistent for replayed events.

### D. Refund validation

Refund processing now checks:

- Refund value type.
- Positive refund amount.
- Cumulative refund amount against the original purchase amount.

**Benefit:**
- Rejects malformed and excessive refunds.
- Protects transaction refund totals from invalid updates.

### E. Proportional refund calculation

The implementation uses cumulative refund value to calculate the total points that should be reversed.

**Benefit:**
- Supports partial refunds.
- Avoids reversing more points than were originally awarded.
- Uses integer arithmetic.

### F. Repeat-transaction grouping

Transactions are grouped by account, date and amount.

**Benefit:**
- Identifies repeated transaction patterns.
- Avoids grouping records belonging to different accounts or dates.
- Provides alerts for human review.

## 3. Trade-offs

| Implementation choice | Benefit | Trade-off |
|---|---|---|
| Integer arithmetic | Accurate and predictable calculations | Requires explicit handling of units |
| Deep copy of account | Preserves input account state | Uses additional memory |
| Processed event ID list | Simple replay protection | Lookup becomes slower as the list grows |
| In-memory transaction storage | Simple implementation | Does not provide persistence |
| Grouping with dictionaries | Efficient grouping | Requires valid and consistent transaction fields |

## 4. Further optimization opportunities

The following are proposed improvements and are not claimed as implemented.

1. **Persistent storage:** Store account balances, transactions and ledger entries in a database.
2. **Database-level idempotency:** Enforce uniqueness of event IDs to protect against concurrent duplicate processing.
3. **Identifier validation:** Reject missing or empty event and transaction identifiers.
4. **Input validation:** Validate purchase amounts and reward-rule values before processing.
5. **Ledger reconciliation:** Add checks to ensure the balance matches the sum of accepted ledger entries.
6. **Scalable repeat detection:** Use database indexes or grouped queries for large transaction datasets.
7. **Automated monitoring:** Track rejected events, refund failures and repeat-alert counts.

## 5. Verification

After the implemented changes, the full test suite reported:

```text
214 passed
```

The test command was:

```bash
python -m pytest -q
```

The baseline result was 147 passed and 67 failed.

The improvements focused on correctness and safe event processing rather than premature performance optimization.