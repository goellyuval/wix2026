# CLAUDE.md

QA automation for the Wix Domains "Can I get this name?" doors: storefront, WHOIS, Business Name Generator and the
public Domain Search API. Python 3.13 · pytest · Playwright.

## How to work

1. **Read before you write.** Before adding or changing a test, read what defines the expected behavior:
   the API docs (`https://dev.wix.com/docs/api-reference/account-level/domains/domain-search/...`, append `.md`
   for a plain-text version), any spec or Figma link you are given, `README.md`, `TEST_PLAN.md` and
   `ARCHITECTURE.md`. If the docs and the real behavior differ, say so; don't silently pick one.
2. **Never test only the happy flow.** Every new feature or test file gets negative and boundary cases too:
   invalid input, empty, too long / exactly at the limit, wrong format, missing auth, unsupported values.
3. **Think about edge cases and suggest them.** When you add or review a test, list edge cases you didn't cover
   and ask which to add. Examples for this domain: no TLD, TLD Wix doesn't sell, uppercase/spaces, non-Latin
   (punycode), 63/64 characters, premium names, location-based results.
4. **Keep UI (e2e) tests lean.** UI tests are slow and flaky, so each one is expensive.
   - Short: one flow per test, open the result page by URL when the flow itself isn't what's under test.
   - Assert one thing if possible. Put contract and data checks in API tests, not UI tests.
   - Prefer an API test whenever it can catch the same bug.

## Conventions
- **Layers:** `src/api` (clients, no assertions) · `src/pages` (page objects: locators + actions, no assertions)
  · `tests/` (assertions only here). Global fixtures in `conftest.py`, layer fixtures in `tests/<layer>/conftest.py`,
  single-class fixtures inside the class.
- **Locators:** `data-hook` attributes and roles (`get_by_role`). Never generated CSS classes.
- **Waits:** Playwright auto-waiting (`expect`, `wait_for`, `wait_for_url`). No `sleep`, no `wait_for_timeout`.
- **Expected values come from real behavior or the docs**, never guessed. Probe once, then assert.
- **Known doc/behavior gaps** are `xfail(strict=True)` with a reason pointing to `FINDINGS.md`.
- **Tags:** every test file sets `pytestmark = [<layer>, pytest.mark.regression]`; add `@pytest.mark.sanity` only to
  fast, critical-path tests. `--strict-markers` is on.
- **Names read as sentences:** `test_free_domain_is_available`, `test_invalid_domain_returns_400[missing_tld]`.

## Commands
```
.venv\Scripts\python.exe -m pytest -m sanity        # before every commit
.venv\Scripts\python.exe -m pytest -m regression    # full suite
.venv\Scripts\python.exe -m pytest --collect-only -q -m <suite>   # check selection, zero API calls
.venv\Scripts\python.exe scripts\triage.py -m sanity               # run + triage (see /triage-suite skill)
```
Debug logs: add `--log-cli-level=DEBUG`. Failure traces: `test-results/` (`playwright show-trace <zip>`).

## Hard rules
- **Never complete a purchase.** Don't click "Make It Yours" / "Get It" / anything that adds to cart.
- **API budget: a few hundred calls in total.** Prefer `--collect-only`, single tests or `-m sanity` over full runs.
  No load testing, brute force or scraping.
- **Secrets:** the key lives only in `.env` (git-ignored). Never print, log, commit or paste it.
- **Never delete a test or commit** without the user's explicit OK. Suggest instead.
- **Keep the real commit history:** small commits, no squashing, no rewriting.
