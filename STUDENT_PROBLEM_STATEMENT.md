# ClubBudget: Student Club Expense and Budget Management

**Zenith School of AI | Open-Source Evaluation | Python 3.10+ | JSON | GitHub**

## Challenge
ClubBudget tracks student-club expenses, categories, vendors, receipt references, approvals and budget limits. Understand the supplied Python application, fix three issue tickets announced by organisers at kick-off, implement reliable search/filtering, add one finance workflow feature, test your work and explain the decisions. Improve the existing code instead of rebuilding it.

## Start-up
```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m main
```
Read README.md, models.py, service.py, fixtures.py, data/ and tests/test_contract.py. Create ARCHITECTURE.md with the project map, data model, numbered flow, storage design, simple diagram and three improvements grounded in the code.

## Mandatory work
1. Reproduce and fix three organiser-provided issue tickets; add regression tests.
2. Implement case-insensitive search with trimmed query text and combined category/status filters. Handle invalid filters, no results and empty data safely.
3. Complete at least one option:
   - Budget dashboard: show approved/paid spending and remaining budget by club/category.
   - Approval safeguards: reject negative amounts and approvals that exceed applicable budget.
   - Receipt audit: identify expenses missing receipt references and flag potential duplicate claims.
4. Add tests and document at least five scenarios in TESTING.md. Update README.md and PROJECT_NOTES.md.
5. Use focused branches and pull requests. Do not delete, skip, weaken or bypass tests.

## Test suite
The public suite contains 110 visible checks. The untouched starter is expected to begin at 86 passing and 24 failing due to deliberate defects. The final evaluation adds 90 private checks, for 200 cases total. Private tests are not included in this public repo.

## Git workflow and submission
Use fix/issue-<number>-<summary> for bug fixes and feature/<short-name> for features. Each pull request must include root cause, summary, issue reference, tests run and known limitations.

Submit your repo/fork and PR links, README.md, ARCHITECTURE.md, TESTING.md, PROJECT_NOTES.md, a summary of fixes/features and a two-minute demo. If AI tools are used, complete AI_USAGE.md with tool/model, purpose, verification performed, any shown credits/tokens (or "not available"), and one suggestion accepted, changed or rejected with a reason. Do not include secrets or private personal data. Be able to explain and modify your code during viva.

## Evaluation — 100 marks

| Criterion | Marks |
|---|---:|
| Codebase understanding | 15 |
| Problem solving and root-cause analysis | 25 |
| Working prototype and requested features | 20 |
| Code quality | 10 |
| Testing and edge cases | 10 |
| Demo, communication and viva | 20 |
| **Total** | **100** |

All 300 students use the same rubric; the top 270 are shortlisted by score, subject to any minimum competency criteria announced by organisers. Follow the official event announcements for kick-off, code freeze, deadlines and demo timings.
