---
name: triage-suite
description: Run the test suite and triage the results. Green → report by category (api, ui/e2e). Not green → for each failure decide flaky, regression from a change, or intended product change; quarantine, suggest a fix or suggest deleting the test; then write a clear report. Use when asked to run, check or triage the tests.
---

# Triage the suite

You triage; the human decides anything destructive. Never delete a test, never edit product code, never commit.

## 1. Run
```
.venv\Scripts\python.exe scripts\triage.py [pytest args]
```
Pick the suite from the request: `-m sanity` (commit check, 6 tests), `-m regression` (nightly, everything),
`-m api` / `-m ui` (one layer). No suite named → `-m sanity`, and say so in the report.
The script runs the suite, reruns each failure 2 times, and writes `reports/triage.json` + `reports/triage.md`.
Read `reports/triage.json`. Each failure has `classification`: `flaky` (passed on a rerun) or `consistent`.
Don't run it more than needed: the whole project has a budget of a few hundred API calls.

## 2. Green
If `green` is true: report totals and the tests per category (api, ui (e2e)), using `reports/triage.md`.
Also list:
- `xfailed` tests: known gaps from FINDINGS.md, expected.
- quarantined tests that **passed**: candidates to release from `tests/quarantine.txt` (suggest, don't remove).
Then stop.

## 3. Not green: classify each failure
Work through these in order and stop at the first that fits. Always quote the evidence (error message, diff, response).

### A. Flaky
`classification == "flaky"`.
1. Find the likely cause in the failure message: timing (`TimeoutError`, hydration), data (generated suggestions,
   random names), network.
2. **Quarantine it:** add one line to `tests/quarantine.txt`:
   `<node_id> | flaky: <short cause> | <today YYYY-MM-DD>`
3. **Suggest a fix** (code snippet), preferring Playwright auto-waiting (`expect`, `wait_for`, event-based waits)
   over sleeps or retries. Don't apply it unless asked.

### B. Regression caused by a change
`classification == "consistent"`. Check for a change that explains it:
1. **This repo:** `git log --since="<date of last green run or 7 days>" --stat` and `git diff <last green commit>`
   for files under `src/` and `tests/`. If `gh` is installed, also `gh pr list --state merged --limit 10`.
2. **The product (Wix):** we can't see Wix's PRs. Use evidence instead: rerun the failing test with
   `--log-cli-level=DEBUG`, compare the API response or the page against what the test expects, and check the Wix
   docs page for the endpoint (changelog / "deprecated" notes).

If a change in **this repo** caused it: treat like flaky (quarantine + suggest the fix or a revert), naming the commit.
If a **product change** caused it and it looks like a bug: quarantine, and draft a finding (steps, expected,
actual, evidence) for `FINDINGS.md`. Don't add it yourself.

### C. Intended product change
Only when there is **evidence the change was deliberate**: a docs or changelog note, a PR description, a release
note, or the feature visibly replaced by a new one (e.g. a filter button removed in a redesign, and the test checks
that button).
- **Suggest deleting or rewriting the test**, with the evidence and the exact test to remove. Never delete it yourself.
- No evidence it was deliberate? Classify it as **"needs human decision"**, not C.

### D. Anything else
Environment problems (missing `.env`, no network, browser not installed): say so and give the fix command.
Don't quarantine environment failures.

## 4. Report
End with this report (in chat; also offer to save it as `reports/triage-report.md`):

```
# Triage report: <GREEN | NOT GREEN> · <suite> · <date>
Totals: <passed> passed · <failed> failed · <xfailed> known gaps · <quarantined> quarantined

| Category | Passed | Failed | Known gaps | Quarantined |

## Failures
| Test | Verdict (flaky / regression: repo / regression: product / intended change / needs human / env) | Evidence | Action taken | Suggested next step |

## Actions taken
- Quarantined: <tests, and the line added to tests/quarantine.txt>

## Needs a human
- <deletions suggested, product bugs to report, decisions>
```

Keep it short. One line per test. Facts first, then your opinion, labeled as such.
