# Implementation Approach — RewardBook

## 1. Understanding the problem

The objective was to implement reliable reward-point processing for captured purchases, refunds and possible repeat transactions.

The implementation needed to ensure:

- Correct reward calculation using integer arithmetic.
- Reward points are awarded only for captured purchases.
- Repeated events do not process the same reward twice.
- Refunds reverse points proportionally.
- The points balance does not become negative through valid refund processing.
- Each accepted purchase or refund event has an auditable ledger entry.
- Similar transactions can be flagged for human review.

## 2. Understanding the existing codebase

The project is organized into separate modules:

- `models.py`: Creates the initial account structure, including balance, processed event IDs, transactions and ledger.
- `fixtures.py`: Provides sample accounts, transactions and reward rules.
- `service.py`: Contains reward calculation, event processing and repeat-transaction detection.
- `main.py`: Runs a sample calculation and repeat-transaction check.
- `tests/`: Contains contract tests and acceptance tests.

The main implementation work was focused on `service.py`.

## 3. Baseline investigation

Before modifying the implementation, the existing test suite was executed.

**Baseline result:**
- Passed: 147
- Failed: 67

The failures highlighted issues in:

- Floor-based reward calculations.
- Bonus and points-cap handling.
- Duplicate event processing.
- Purchase transaction consistency.
- Refund validation and amount boundaries.

The baseline output was preserved in `baseline-test-results.txt`.

## 4. Implementation decisions

### A. Reward calculation

Replaced floating-point rounding with integer floor division.

The calculation now applies the bonus percentage before applying the optional cap. A cap of zero is treated as a valid value.

### B. Event idempotency

Added a check against previously processed event IDs.

If an event ID has already been processed, the account state is returned without applying the event again.

### C. Refund validation

Added checks to reject:

- Non-integer refund amounts.
- Zero or negative refund amounts.
- Refunds that exceed the remaining refundable purchase amount.

### D. Proportional refund reversal

The implementation calculates the cumulative points that should be reversed based on the cumulative refunded amount.

Only the difference between the newly calculated reversal and the previous reversal is deducted from the balance.

### E. Repeat-transaction detection

Transactions are grouped using:

- Account ID.
- Transaction date.
- Transaction amount.

A group is flagged when its transaction count exceeds the configured threshold.

## 5. Verification

The implementation was checked using the existing contract and acceptance test suites.

The verified full-suite result was:

```text
214 passed
```

The test command used was:

```bash
python -m pytest -q
```

The Python environment used was Python 3.14.4.

## 6. Scope and limitations

The implementation focuses on the supplied in-memory account and transaction structures.

The following areas require further work:

- Explicit validation of missing event and transaction identifiers.
- Validation of malformed purchase amounts and reward-rule types.
- Persistent storage and concurrent event-processing safety.
- Additional tests for malformed purchase events and missing identifiers.