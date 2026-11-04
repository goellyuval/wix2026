# Wix Domains QA: "Can I get this name?"

**Time spent: about 3 hours in total**, including environment setup (Git, Python, Wix account, API key) before the
first commit.

QA home assignment for Wix Domains: understanding, test plan, exploration and automation for the four doors that
answer "Can I get this name?": the domain storefront, WHOIS lookup, Business Name Generator and the public
Domain Search API.

| Document | What's in it |
|---|---|
| [ARCHITECTURE.md](ARCHITECTURE.md) | What each door is made of, its network calls, what each call drives on screen, diagram |
| [TEST_PLAN.md](TEST_PLAN.md) | Risks and priorities, approach, cases by door with status, what's left out and why |
| [FINDINGS.md](FINDINGS.md) | 5 findings with evidence, severity and priority, plus observations |
| [AI_LOG.md](AI_LOG.md) | How AI was used, where it was wrong, what I kept for myself |
| [CLAUDE.md](CLAUDE.md), [.claude/skills/triage-suite](.claude/skills/triage-suite/SKILL.md) | Agent configuration: working rules and the suite-triage skill |

## How to run the tests

**Prerequisites:** Python 3.13, a free Wix account and an [account-level API key](https://manage.wix.com/account/api-keys).

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m playwright install chromium
copy .env.example .env        # then fill in WIX_API_KEY and WIX_ACCOUNT_ID
```

**Run everything (single command):**
```
.venv\Scripts\python.exe -m pytest
```

**Suites** (tags, combinable with `and` / `or` / `not`):

| Command | Suite | Tests |
|---|---|---|
| `pytest -m sanity` | Every commit: fast critical path | 6 |
| `pytest -m regression` | Nightly: everything | 32 |
| `pytest -m api` / `pytest -m ui` | One layer | 26 / 6 |

**Debugging:** `--log-cli-level=DEBUG` prints every request, status, timing and response body (never the key).
Failing UI tests leave a Playwright trace and screenshot in `test-results/` (`playwright show-trace <zip>`).

**Triage:** `.venv\Scripts\python.exe scripts\triage.py -m sanity` runs a suite, reruns failures to separate flaky from
consistent, and writes `reports/triage.md`. The `/triage-suite` skill adds the judgment: quarantine
(`tests/quarantine.txt`), PR and change check, fix suggestions, and a final report.

**Expected result today:** all green, plus 6 `xfail` tests. Those are known differences from the docs
(`FINDINGS.md`), marked `strict` so they start failing, as a signal, if Wix changes the behavior.

> The tests run against production wix.com and the public API. Keep runs small: the assignment budget is a
> few hundred API calls in total. Use `-m sanity` or `--collect-only` when you only need a check.

## Automation choices

| Choice | Why |
|---|---|
| **API deep, UI lean** (26 API vs. 6 UI cases) | All three web doors call the same `domain-search/v2` endpoints, so API tests cover the core answer of every door, fast and stable. UI tests are slow and flaky, so each one is short, asserts one thing, and opens results by URL unless the search flow itself is under test. |
| **UI answer = API answer** | The most valuable UI test: it catches the doors disagreeing (risk R2) without asserting generated content. |
| **Contract, not content** | Suggestions and prices change by design. Tests check limits, formats, filters and availability, never exact names or prices. |
| **Expected values from real behavior** | Every negative case was probed against the live API first; no guessed error messages. |
| **Known gaps as strict `xfail`** | Documents the gap in the code and flags any change in either direction. |
| **Page objects + API client, no assertions inside** | Locators and calls are in one place; tests read as arrange / act / assert. |
| **Stable locators, auto-waits** | `data-hook` attributes and roles, never generated CSS classes. No sleeps; one measured `networkidle` wait for the search-box hydration issue (FINDINGS F2). |
| **Fixtures by reach** | Global for shared clients and test data, `tests/ui/conftest.py` for pages, class-local for auth-only clients. |

```
src/api/      API client (requests session, logging)      src/pages/  page objects
src/utils/    test data helpers                           tests/api/  tests/ui/   tests, one class per feature
conftest.py   global fixtures + quarantine hook           scripts/triage.py   suite triage runner
```

## What I'd do with another week
- **CI:** sanity on every pull request, regression nightly, API key in repository secrets, triage report as an artifact.
- **Coverage I couldn't reach:** a second location (VPN) for currency, TLDs and "Best Match" (R8); an available
  premium domain and its price display; mobile and touch (hover-only pricing, F4); Firefox and WebKit.
- **More UI checks, still lean:** card price = price-service response; WHOIS registered / unregistered smoke tests;
  Business Name Generator → domains available.
- **Contract tests:** JSON schemas for both endpoints, run against the docs' examples too.
- **Report the findings** to the owning teams and turn F1 (auth) into a decision: fix the gateway or the docs.
- **Simplify the architecture diagram** into an overview plus one sequence diagram.

## Quality strategy for Wix Domains, in 5 lines
1. Availability has one source of truth (`domain-search/v2`), so test it deepest, at the API, where bugs are cheapest to catch.
2. Test that the doors agree with that source, and that the contract holds; never assert generated suggestions or prices.
3. Keep UI tests few, short and one-assertion: sanity on every commit, regression nightly.
4. Treat the docs as a contract: every gap is a visible, strict test, so drift in either direction raises a flag.
5. Explore before automating, feed what you learn back into the plan, and triage failures: quarantine flaky tests, never silently delete.
