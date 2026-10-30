# RewardBook: Rewards Rules & Repeat-Transaction Alerts

**Track:** Fintech loyalty | **Time:** 24 hours | **Language:** Python 3.10+

## Scenario
A loyalty product awards points for eligible purchases. Promotions may add a bonus or cap. Purchases can later be refunded; duplicate transaction events must not award points twice. Operations also need transparent warnings for possible same-account, same-day, same-amount repeats.

This is a fictional offline service inspired by common rewards products. It is not any company's internal code and uses no real financial/customer data.

## Required behaviour
1. Calculate points using integer arithmetic: base_points = floor(amount_paise / 10000) * points_per_100_rupees; bonus_points = floor(base_points * (100 + bonus_percent) / 100); apply optional cap_points last.
2. Invalid or negative amounts/rules must not generate points. A cap of zero means zero points.
3. Only captured purchases earn points. Declined, pending and unknown events must not.
4. Process each event_id once so replaying purchase/refund events cannot alter balances twice.
5. Reverse points proportionally for refunds using integer arithmetic, never reverse more than awarded and never allow a negative balance.
6. Write an auditable ledger entry for each accepted purchase/refund event.
7. Flag possible repeats by account, date and amount using the supplied threshold. Alerts are for human review only; never block a transaction or automatically accuse a customer.
8. Handle empty input, missing identifiers, unknown transactions and boundary values safely.

## Setup
Run: `python -m pip install -r requirements-dev.txt`, then `python -m pytest -q`, then `python -m main`.

## Repository reading checklist and dataset

Before editing, read `README.md` and `STUDENT_START_HERE.md`, then inspect the whole repository—not only this PDF. Read `CONTRIBUTING.md`, `.github/PULL_REQUEST_TEMPLATE.md`, the test/template documents, `service.py`, `models.py`, `fixtures.py`, `main.py`, every file under `tests/`, and the workflow files under `.github/workflows/`.

The expanded synthetic dataset is in `data/records.json`: **40 accounts, 180 repeat-pattern transaction records, 264 reward event examples, 180 captured-purchase records, and 8 reward-rule cases**, plus an edge-case catalog. Read `data/README.txt` for its schema. The dataset includes groups of repeated same-account/date/amount purchases, rounding boundaries, caps, malformed values, duplicate events and refund edge cases. The offline demo uses `fixtures.py`; the larger JSON is additional investigation and test material. All records are synthetic.

Run the baseline tests before editing and record their actual result. Never weaken tests just to remove failures.

## Work to submit
- Read the source and run the starter tests before editing.
- Use the requirements and tests as the acceptance contract. Trace failures to their root causes, fix the underlying behaviour, and avoid hard-coding sample output.
- Add regression tests and document at least five edge cases in `TESTING.md`.
- Submit one pull request to the original repository with the fixes, tests and a brief explanation. Do not merge it.
- Include `REWARD_RULE_NOTES.md` with one worked points calculation, one partial-refund example and three edge cases.

## Mandatory problem-solving documentation — all three files required
Submit these three completed Markdown files at the repository root in your pull request. They are evaluated; code alone is not a complete submission.

- `approach.md` — record your starting test result, the code/data flow you explored, key hypotheses, experiments you ran, implementation strategy, and why you chose it.
- `challenges.md` — **COMPULSORY**. Describe concrete obstacles or confusing behaviours, what you tried, evidence from tests/logs, how you resolved them, and any unresolved limitations. If you did not get stuck, state that honestly and describe the hardest edge case you deliberately tested; do not invent a struggle.
- `optimizations.md` — describe optimizations considered or implemented, why you chose or rejected them, correctness/readability/performance trade-offs, and future improvements. Separate measured improvements from ideas you did not measure.

Keep the notes concise, specific and evidence-based. Describe your actual work, tests and technical decisions; do not provide private hidden chain-of-thought or a stream-of-consciousness transcript. Generic or copied text does not demonstrate your process. Each file is worth 5 marks. A missing or empty file receives 0/5 for that component and makes the documentation requirement incomplete.

## Optional stretch work
Choose at most one: generate a CSV account statement; make the repeat threshold configurable; or add a rewards summary by category.

## Testing and GitHub Actions
The untouched starter is expected to have some failing visible tests because behaviours are incomplete. The exact test count is not fixed. GitHub Actions runs on pushes and pull-request updates and publishes test counts. A red check before fixes is expected; make the visible tests pass without deleting, skipping, weakening or bypassing them. Do not alter the workflow to evade failures.

## Final submission checklist — complete every item

Before the deadline, verify each item below. **A code change alone is not a complete submission.**

- [done ] I read this problem statement, `STUDENT_START_HERE.md`, `README.md`, the contribution guide, all relevant source files, the synthetic data documentation, every visible test, and the GitHub Actions workflow.
- [ done] I ran `python -m pip install -r requirements-dev.txt`, recorded the untouched baseline result from `python -m pytest -q`, and ran `python -m main`.
- [done ] I fixed the underlying causes of relevant failures and added regression tests. I did not delete, skip, weaken, hard-code around, or bypass existing tests or edit CI to hide failures.
- [done ] I completed the existing `approach.md`, `challenges.md`, and `optimizations.md` templates at the repository root. Each must describe my own work and evidence; `challenges.md` is compulsory. Each is worth 5 marks.
- [ done] I completed `TESTING.md` with the real Python version, commands and test summary, plus at least five edge cases showing input, expected behaviour, actual result, and test/evidence.
- [done ] I completed `REWARD_RULE_NOTES.md`. Include (1) one worked points calculation from purchase amount through bonuses/caps, (2) one partial-refund/reversal example, (3) assumptions, and (4) at least three edge cases.
- [done ] I reviewed the diff, kept the change focused, and ensured I did not commit secrets, credentials, or unrelated files.
- [ done] I opened **one pull request from my fork to this original repository**, included code, tests and all required documents, filled in the pull-request template, and **did not merge the pull request**.
- [done ] I checked the pull-request CI result and documented any remaining failures honestly.
- [ done] I can explain the changes independently and make a small live modification if requested.

If any item is incomplete, finish it before submitting. Record actual results only; never claim a test passed unless it was run. Follow the individual-work and AI-use policy below.

## Mandatory problem-solving files — submit all three

You must complete **all three files** below in the root of your assigned repository and include them in your pull request. These are required deliverables and together are worth **15 marks** in the evaluation rubric (5 marks each). Start from the provided repository templates, replace the placeholder prompts with your own work, and commit the completed files. A blank template or generic, unsupported text does not count as completion.

### 1. `approach.md` — approach and implementation decisions (5 marks)

Explain your engineering approach in your own words:
- How you understood the problem and traced the relevant code/data flow.
- The root cause you identified and the evidence that led you to it.
- The solution options you considered and why you selected your approach.
- Important implementation decisions, experiments, and how you validated the fix.

### 2. `challenges.md` — challenges and debugging (5 marks; compulsory)

Record the real challenges you faced while investigating and solving the task:
- The specific technical issue or obstacle.
- What you tried, what worked or failed, and how you investigated it.
- Evidence such as reproduction steps, relevant error/test output, or code references.
- How you resolved the issue and any remaining limitations.

Do not invent problems or results. If you did not encounter a major obstacle, explain a genuine investigation or tricky edge case you worked through and support it with evidence.

### 3. `optimizations.md` — optimizations and trade-offs (5 marks)

Describe improvements and engineering trade-offs:
- Which optimizations you considered and which you actually implemented.
- Why an optimization is useful, with test results or other evidence where possible.
- Trade-offs, risks, complexity, performance, or maintainability considerations.
- What you would improve next and why, if more time were available.

### Documentation submission rules

- Use your own words and document work you actually performed; do not copy another student's work.
- Be concrete and evidence-based. Reference the tests you ran and report their actual outcomes—never claim a test passed unless you ran it.
- Include all three completed files in the same pull request as your code and tests.
- **Missing, empty, or materially incomplete files can receive zero for the relevant 5-mark component and may make the submission incomplete.**
- You must be able to explain your decisions and evidence during the evaluation. This asks for an engineering record, not a private chain-of-thought transcript.

## Individual-work policy
AI chatbots, AI coding assistants, generated patches/tests and third-party solution-writing are prohibited. Normal non-AI documentation is allowed. Do not upload assessment code or data to external services. You must explain your changes and make a small live modification if asked. A walkthrough supports integrity review; automated AI detectors are not definitive proof of use.

## Rubric — 100 marks
- Understanding code and data flow: 10
- Points calculation and business-rule correctness: 20
- Idempotency, refunds, ledger integrity and repeat alerts: 25
- Testing and root-cause analysis: 15
- Code quality and maintainability: 5
- Required problem-solving documentation: 15 (approach.md: 5, challenges.md: 5, optimizations.md: 5)
- Pull request, rewards notes and live explanation: 10

The three process documents are assessed for specific, honest, evidence-based technical reflection, not writing style.
