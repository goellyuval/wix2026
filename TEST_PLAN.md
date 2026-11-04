# Test Plan: Wix Domains, "Can I get this name?"

**Owner:** Yuval Goell · **Last updated:** 2026-11-04 · **Tested from:** Israel (₪, browser language Hebrew), Chromium

## 1. Goal and scope
Every door must give the user a **correct, consistent and usable** answer to "Can I get this name?".

| Door | URL | Priority |
|---|---|---|
| Public Domain Search API | `GET https://www.wixapis.com/domain-search/v2/{check-domain-availability, suggest-domains}` | P0 |
| Domain storefront | https://www.wix.com/domains | P0 |
| WHOIS lookup | https://www.wix.com/domains/whois | P1 |
| Business Name Generator | https://www.wix.com/tools/business-name-generator | P1 |

**Why the API first:** all three web doors call the same `domain-search/v2` endpoints (seen in DevTools).
Testing the API deeply covers the core logic behind every door.

## 2. Risks and priorities
Priority = user/business impact × likelihood.

| # | Risk | Impact | Priority | Covered by |
|---|---|---|---|---|
| R1 | Wrong availability answer | Lost sale, broken trust | **P0** | API + UI automation, manual |
| R2 | Doors disagree on the same name | Confusion, support load | **P0** | UI-vs-API test, manual cross-door |
| R3 | Bad input handling (no TLD, `.com` vs `com`, characters, length) | Errors, dead ends | **P0** | API automation, manual |
| R4 | Wrong price / premium not flagged | Revenue loss, surprise charge | P1 | Manual (premium: **gap**, see §7) |
| R5 | Search slow or silently does nothing | User drops off | P1 | Manual (timings), UI automation |
| R6 | Suggestions invalid or not really available | Dead-end upsell | P1 | API automation |
| R7 | API behavior differs from its docs (fields, enums, auth, limits) | Integrators break | P1 | API automation (strict xfail) |
| R8 | Location changes what users see (currency, TLD order, "Best Match") | Other markets untested | P1 | Manual, one location only |
| R9 | Pricing terms shown only on hover (renewal, plan condition, .ai minimum) | Surprise at renewal | P1 | Manual |

R8 and R9 were added after manual exploration (§5).

## 3. Approach

| Layer | What | Why |
|---|---|---|
| **API automation (deep)** | Contract, validation, auth, suggestion validity | Fast, stable, cheap; covers logic behind all doors |
| **UI automation (shallow)** | Storefront: taken vs. free, and **UI answer = API answer** | Real pages are slow and change; keep a few high-value flows on stable locators (`data-hook`, roles) |
| **Manual exploratory** | All doors, edge input, pricing, cross-door, network + console | Needs judgment; fastest way to learn the system |

**Test data:** taken = `google.com`; free = `qa-<random>.com` (new per test). No assertions on generated
suggestion content or on exact prices.
**Oracles:** the public API for availability; the price service response for displayed prices; WHOIS for "registered".

## 4. Test cases by door
Status: ✅ passed · ❌ issue found · ⚠️ partial/risk · ⬜ not run · 🤖 automated

### 4.1 Public API
| Case | Expected | Status |
|---|---|---|
| Taken domain | `available: false` | ✅ 🤖 |
| Random new domain | `available: true`, `premium: false` | ✅ 🤖 |
| Response fields and types | `domain`, `available`, `premium`, `premiumType` | ✅ 🤖 |
| Uppercase input | Returned lowercase | ✅ 🤖 |
| 63-char name / 64-char name | 200 / 400 `DOMAIN_TOO_LONG` | ✅ 🤖 |
| Punycode (`xn--8db5ai.com`) | 200 | ✅ 🤖 |
| Invalid: no TLD, unknown TLD, empty, `_`, edge hyphens, raw unicode | 400 with specific message | ✅ 🤖 |
| TLD Wix doesn't sell (`.gov`) | 400 `DOMAINS_UNSUPPORTED_TLD` | ✅ 🤖 |
| `premiumType` uses documented values | In documented enum | ❌ 🤖 `UNKNOWN_PREMIUM_TYPE` |
| No key / no account ID / fake key | 401/403 per docs | ❌ 🤖 returns 200 |
| Suggestions: limit, count, valid `name.tld`, TLD filter, `.com` rejected | Per docs | ✅ 🤖 |
| Suggested domains are really available | `check-domain-availability` agrees | ✅ 🤖 |

### 4.2 Domain storefront
| Case | Expected | Status |
|---|---|---|
| Taken name | "already registered" + alternatives | ✅ 🤖 |
| Free name | "Exact Match · Available now!" + correct price | ✅ 🤖 |
| No TLD (`sunnybaker`) | Suggestions only | ✅ |
| TLD Wix doesn't sell | Clear message + supported TLDs link | ✅ 🤖 |
| Spaces + mixed case | Trimmed and normalized everywhere | ⚠️ only in the availability call |
| Hebrew name | Converted to punycode | ✅ |
| 64-char name | Clear, correct limit message | ❌ 🤖 says "fewer than 63", suggests 63-char names |
| Search right after page load | Works | ❌ silently ignored until the page finishes loading |
| Renewal price and conditions | Visible before cart | ⚠️ only in a hover tooltip |
| Suggestions load time | Fast | ⚠️ 2–5 s (availability ~0.4 s) |
| Premium name with price | Premium label + price | ⬜ no available premium name found |

### 4.3 WHOIS lookup
| Case | Expected | Status |
|---|---|---|
| Registered domain | Record shown, contacts redacted | ✅ |
| Unregistered domain | Clear "not registered" | ✅ redirects to storefront "Available now!" |
| Hebrew domain | Same answer as storefront | ✅ |
| Invalid input | Validation message | ⬜ |

### 4.4 Business Name Generator
| Case | Expected | Status |
|---|---|---|
| English description | Names + domains | ✅ |
| Hebrew description | Names + domains | ✅ (English names, `.co.il` first) |
| Shown domains are available | API agrees | ✅ (`bakerybloom.com`, `.co.il`) |
| Empty / very long input | Validation | ⬜ |

### 4.5 Cross-door consistency (R2)
Same answer on storefront, WHOIS and API for `google.com`, `קפה.com` and `qa-…` names: ✅ no disagreement found.
**Allowed differences (not bugs):** generated suggestions, location-based prices/TLDs, point-in-time availability.

## 5. Exploration notes
Run on 2026-11-04 in the in-app browser, reading network and console at every step.

**How the storefront routes input:**

| Input | What the storefront does |
|---|---|
| Valid name + TLD | `check-domain-availability` + `suggest-domains` + price service |
| No TLD | **Skips** the availability check; suggestions only |
| Unsupported TLD | Availability returns 400 → friendly message |
| Non-Latin | Converts to punycode before calling the API |
| Too long | Blocked in the browser; availability never called |

**What exploration changed:**
- Added **R8** and **R9**; raised R5 after measuring suggestion latency.
- Added the **punycode** API test: I first assumed the API doesn't support non-Latin names.
- Downgraded **`premiumType`**: `UNKNOWN_PREMIUM_TYPE` only appears when `premium: false`, so it is a missing
  docs value, not a broken contract.
- Corrected my own conclusion: network data suggested the renewal price was hidden; the UI shows it in a tooltip.
- Found the **search-after-load** issue through a flaky automated test, then confirmed it with measurements.

## 6. Automated coverage

| File | Class | Risks |
|---|---|---|
| `tests/api/test_check_availability.py` | `TestCheckAvailability` | R1, R3, R7 |
| `tests/api/test_suggest_domains.py` | `TestSuggestDomains` | R3, R6 |
| `tests/api/test_authentication.py` | `TestAuthentication` | R7 |
| `tests/ui/test_storefront_search.py` | `TestStorefrontSearch` | R1, R2, R5 |

Known differences from the docs are `xfail(strict=True)` tests: they document the gap and start failing
(as a signal) if the behavior changes. Details in `FINDINGS.md`.

## 7. Out of scope and gaps

**Out of scope, by choice:**

| Item | Why |
|---|---|
| Checkout, payment, purchases | Forbidden, and outside "can I get this name?" |
| Load / performance testing | Forbidden; I only record timings I observed |
| Multiple locations | One machine, one location (Israel) |
| Cross-browser, mobile | Time-boxed; Chromium only |
| Accessibility audit | Time-boxed |
| Exact suggestion content | Generated by design |
| Security beyond auth basics | Out of a 3-hour scope |

**Gaps, not by choice:**
- **Premium price display:** every premium name I found was already taken.
- WHOIS and Generator invalid input (⬜ above).
- Hover-only pricing on touch devices (mobile not tested).

## 8. Open questions
- Is anonymous API access intentional (the storefront uses the same endpoints without a key) or an auth gap?
- Should `suggest-domains` accept a query that includes a TLD? The docs say no; the storefront sends one.

## 9. Next steps
1. ~~UI test for the 63-character limit message~~ (done: strict xfail).
2. UI check that the card price equals the price service response.
3. WHOIS smoke test (registered → record; unregistered → storefront).
4. Find an available premium name and test its display.
5. Run from a second location (VPN) to cover R8.

## 10. Exit criteria
All P0 cases run, findings logged with evidence, API + storefront automation green with one command,
and gaps listed in §7.
