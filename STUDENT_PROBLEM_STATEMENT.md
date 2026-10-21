# RewardBook: Rewards Rules & Repeat-Transaction Alerts

**Track:** Fintech loyalty | **Time:** 24 hours | **Language:** Python 3.10+

## Scenario
A loyalty product awards points for eligible purchases. Promotions may add a bonus or cap. Purchases can later be refunded; duplicate transaction events must not award points twice. Operations also need explainable warnings for possible repeat same-account, same-day, same-amount transactions.

This is a fictional offline service, not any company's internal software. Use only the synthetic fixtures; do not connect to cards, banks or customers.

## Required behaviour
1. Calculate points using integer arithmetic: `base_points = floor(amount_paise / 10000) * points_per_100_rupees`; `bonus_points = floor(base_points * (100 + bonus_percent) / 100)`; apply optional cap last.
2. Reject invalid or negative amounts/rules. A cap of zero means zero points.
3. Only captured purchases can earn points. Declined/pending/unknown event types must not.
4. Process each `event_id` once, even if replayed.
5. Reverse points proportionally on refunds using integer arithmetic; never reverse more than awarded and never allow a negative balance.
6. Write an auditable ledger entry for each accepted event.
7. Flag repeats by account, date and amount using the threshold; flags are for human review only and must not block or accuse customers.
8. Handle empty input, missing IDs, unknown transactions and duplicate deliveries safely.

## Kick-off tickets
At kick-off organisers will share three concrete issue tickets from the project. Reproduce each issue, explain the root cause, fix it and add a regression test. Example defect classes: wrong rounding, cap-of-zero handling, duplicate event processing, or unsafe refunds.

## Submission
Open a pull request against the original repository; do not merge it. Include tests and `REWARD_RULE_NOTES.md` with one worked points calculation, one partial-refund example, three edge cases, assumptions and limitations. Explain the root cause and tests in the PR.

## Optional stretch (choose at most one)
- Export a CSV account statement.
- Make the repeat threshold configurable.
- Add a summary by transaction category.

## Tests and CI
Run `python -m pytest -q`. Initial visible failures are intentional only for incomplete starter behaviour; no fixed baseline count is promised. GitHub Actions should run for pushes and pull-request updates. A green check means all visible tests passed; it does not replace review of your explanation and code quality. Do not change the workflow or hard-code fixture output to evade checks.

## Integrity policy
AI chatbots, AI coding assistants, generated patches/tests and having another person write/debug the solution are prohibited. Ordinary non-AI documentation is allowed. Do not paste assessment code or data into external services. You must explain your changes and make a small live modification. Organisers may use a brief oral/code walkthrough; automated AI detectors are not definitive proof of AI use.

## Rubric — 100 marks
- Understanding code and data flow: 15
- Correct points calculation and financial edge cases: 25
- Idempotency, refunds and ledger integrity: 25
- Testing and root-cause analysis: 15
- Code quality: 10
- PR, notes and live explanation: 10
