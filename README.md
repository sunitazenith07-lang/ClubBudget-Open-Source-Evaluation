# RewardBook — Rewards Rules & Repeat-Transaction Alerts

> **Central student guide:** [Read the complete Open-Source Evaluation Guide](https://github.com/sunitazenith07-lang/LabLedger-Open-Source-Evaluation/blob/main/OPEN_SOURCE_EVALUATION_STUDENT_GUIDE.md) — includes all four tracks, required reading, submission instructions, and the three compulsory documentation files.

Zenith School of AI | Individual Open-Source Evaluation | Python 3.10+ | Synthetic challenge data only

Fintech loyalty: points formulas, promotional rules, refund reversals, audit ledger and repeat alerts.

## Start here — read before coding

**Start with the [Student Reading Checklist](STUDENT_START_HERE.md).** It lists the required reading and every deliverable.

- **[Open problem statement PDF](docs/Problem_Statement.pdf)**
- [Read the full Markdown problem statement](STUDENT_PROBLEM_STATEMENT.md)
- [Open all student instructions and required-file checklist](STUDENT_START_HERE.md)

## Setup

1. Install Python 3.10+ and Git.
2. Install dependencies: `python -m pip install -r requirements-dev.txt`
3. Run the test suite: `python -m pytest -q`
4. Run the offline application demo: `python -m main`

Final reported verification: `python -m pytest -q` completed with `225 passed in 2.12s`.

Most recently reported demo output:

```text
Points example: 27
Repeat warnings: []
```

The demo uses the sample rules and transactions from `fixtures.py`. The larger `data/records.json` dataset is additional investigation and test material; it is not loaded by `python -m main`.

The repository began with intentionally incomplete starter behavior, but the current reported test run passes. Never delete, skip, weaken or bypass tests to make the check green.

The final regression additions cover missing, `None`, and non-integer purchase amounts without financial mutation, plus accepted zero-amount purchases.

## Mandatory submission — code plus documentation

Submit one pull request from your fork to this original repository; **do not merge it**. Read [CONTRIBUTING.md](CONTRIBUTING.md) and follow the [pull-request checklist](.github/PULL_REQUEST_TEMPLATE.md).

You must complete all three Markdown documents; they are part of the 100-mark evaluation:

- [`approach.md`](approach.md) — 5 marks
- [`challenges.md`](challenges.md) — **COMPULSORY**, 5 marks
- [`optimizations.md`](optimizations.md) — 5 marks

Also submit `TESTING.md` and the challenge-specific notes file named in [the problem statement](STUDENT_PROBLEM_STATEMENT.md). Code alone is not a complete submission. All notes must reflect the work you actually performed.

## Review the whole codebase

Before editing, read the student checklist and inspect the source files, synthetic data, every test under `tests/`, environment/configuration files, and the workflows under `.github/workflows/`. Understand what each file does before changing it.

The starter contains intentionally incomplete behaviour. Fix root causes and preserve the tests. Do not edit CI to evade failures. You must be able to explain your code and may be asked to make a small live modification.
