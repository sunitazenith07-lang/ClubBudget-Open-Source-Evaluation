# Contribution workflow

1. Start when the organiser announces the evaluation.
2. Read `STUDENT_PROBLEM_STATEMENT.md` and inspect source code and tests.
3. Create a focused branch such as `fix/refund-validation` or `feature/rewards-summary`.
4. Run `python -m pytest -q`; never delete, skip or weaken tests.
5. Complete `approach.md`, `challenges.md`, and `optimizations.md` from the repository templates. All three are mandatory and assessed; `challenges.md` is explicitly compulsory.
6. Complete `TESTING.md` and `REWARD_RULE_NOTES.md` as required by the problem statement.
7. Open one pull request to the original repository. Do not merge it. Include the three process files in the PR and mention them in your summary.
8. Include root cause, changes, tests run, assumptions and known limitations. Be ready to explain and modify your code during the live walkthrough.

## Documentation quality
The three process files are worth 15 marks total (5 each). Record what you actually investigated, which tests or logs you used, what you tried, and why you accepted or rejected an approach. Do not invent obstacles or performance measurements. If you did not encounter a blocker, say so honestly and describe your most demanding test. Describe observable technical reasoning; no private hidden chain-of-thought transcript is required.

## Individual-work and AI policy
AI chatbots, AI code-completion/generation, generated patches/tests and another person's solution-writing/debugging are prohibited. Ordinary non-AI documentation is allowed. Do not upload challenge code/data to external services.
