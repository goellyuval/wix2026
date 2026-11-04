# AI Log

## Tools
| Tool | Used for |
|---|---|
| **Claude Code** (Claude Opus 5.5, Claude desktop app) | Pair-working the whole assignment: environment setup, API probing, code, docs, commits |
| **Claude Code built-in browser** | Guided manual testing: I clicked through the doors, the AI read the network calls, responses and console |
| **Agent configuration I wrote** | [CLAUDE.md](CLAUDE.md) (working rules) and [.claude/skills/triage-suite](.claude/skills/triage-suite/SKILL.md) (suite triage skill) |

## How I worked with it
I set the direction and the rules; the AI proposed, probed and wrote; I reviewed before every commit
("show me before commit"). Two rules I applied throughout:
- **No expected value without evidence.** Every assertion was checked against the live API or page first.
- **The AI must say when it isn't sure.** Several corrections below came from the AI re-checking its own claims
  when asked to verify.

## Key prompts
| Prompt (my words, lightly edited) | What it produced |
|---|---|
| "The project should be in Python, pytest + Playwright." | Stack choice (mine, because I know Python best) |
| "Let's build the project with a clear page object structure, global fixtures, local fixtures, page infra and test classes." | `src/api`, `src/pages`, `conftest.py` layout |
| "Can we create a session so you can see my console?" | Guided manual testing in the built-in browser with live network and console reading |
| "Make sure to use smart waits, not sleeps. Are we using fixtures and env vars the proper way? What can be more local?" | Replaced a retry workaround with a measured wait; moved fixtures to the right scope; fixed a connection leak |
| "Create a skill for triaging the suite results: green report by category; if not green, check flaky / PR regression / removed on purpose; clear report." | `triage-suite` skill + `scripts/triage.py` + quarantine list |
| "Add tags so we can divide into suites: sanity for commits, regression for nightly, API." | `sanity` / `regression` markers, `--strict-markers` |
| "CLAUDE.md: read docs first, never test only the happy flow, suggest edge cases, keep UI tests lean, one assertion." | `CLAUDE.md`, then applying it to our own tests: 2 UI tests trimmed, 2 negative UI tests added |

## Where the AI was wrong and how it was caught
| # | What the AI said or did | How it was caught | Outcome |
|---|---|---|---|
| 1 | Called the renewal price **"hidden"**, from network data alone | I hovered the ⓘ icon in the browser and the renewal price was there | F4 downgraded from "hidden price" to "disclosed only on hover" |
| 2 | Wrote that `fill()` on the search box **never works** | Asked to verify, it re-tested: failed 1 of 2 runs, a timing race | Comment corrected |
| 3 | Then claimed typing key by key was **"stable"** | The full suite failed on that test | Root cause measured (page not hydrated), became finding F2 |
| 4 | First fix was a **retry loop**, hiding the problem | My "smart waits, not sleeps" review | Replaced with a measured `networkidle` wait; the retry was thrown away |
| 5 | Assumed the API **doesn't support non-Latin domains** | Manual testing showed the storefront converts to punycode | Added `test_punycode_domain_is_accepted` |
| 6 | Treated `UNKNOWN_PREMIUM_TYPE` as a **contract bug** | More data: it only appears when `premium: false` | Downgraded to a docs gap (observation) |
| 7 | Auth tests created API clients **without closing them** | Fixture review I asked for | Class-local `make_api` fixture that closes them |
| 8 | Wrote **"7 xfail"** in the README | Counted with `--collect-only` before committing | Corrected to 6 |
| 9 | Named a helper script `inspect.py`, which shadowed Python's `inspect` module | Immediate crash | Renamed |
| 10 | First architecture diagram: correct but **unreadable** (about 20 crossing arrows) | Checked on GitHub before submission | Listed as a "next week" item |
| 11 | Quarantine-report table broke on multi-line error messages | Tested the triage skill on demo tests | Messages trimmed to one line |
| 12 | Our own UI tests broke the CLAUDE.md rules we had just written (2 assertions each, no negative UI test) | Applying the new rules to existing code | Trimmed to one assertion, added `.gov` and 64-character UI tests |

## What I changed or threw away
- **Threw away:** the search retry workaround; `tests/api/conftest.py` (fixtures moved to global once UI tests
  needed them); a second assertion in two UI tests; the `alternatives` locator once nothing used it.
- **Changed:** severity ratings after more evidence (F4, `premiumType`); test names rewritten to read as sentences;
  the test plan reorganized into a living plan with a status per case; the API tests extended from happy flow to
  boundaries, invalid input and auth.
- **Kept out on purpose:** load tests, any purchase step, and assertions on generated suggestions or exact prices.

## What I chose not to hand to AI
- **The API key.** I created it and typed it into `.env` myself. It was never pasted into the chat, and the AI
  checked only its length, never its value.
- **Severity and priority calls, and which 5 findings to report.** The AI proposed; I decided (e.g. F1 as
  Medium severity / High priority, because the data is public anyway).
- **Scope and stack:** Python + pytest + Playwright, API deep / UI lean, which suites exist.
- **Commit timing and content:** every commit was made only after I said so.
- **Manual testing:** I did the clicking in the browser; the AI read what happened behind it.
- **Final review:** I read every file before submitting and can explain every line.
