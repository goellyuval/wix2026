# Test Plan: Wix Domains, "Can I get this name?"

## 1. Goal
Make sure every door gives the user a **correct, consistent and usable** answer to "Can I get this name?",
and that a wrong answer is caught before users see it.

| Door | URL |
|---|---|
| Domain storefront | https://www.wix.com/domains |
| Business Name Generator | https://www.wix.com/tools/business-name-generator |
| WHOIS lookup | https://www.wix.com/domains/whois |
| Public Domain Search API | `GET https://www.wixapis.com/domain-search/v2/{check-domain-availability, suggest-domains}` |

## 2. Risks and priorities
Priority = user/business impact × likelihood.

| # | Risk | Impact | Priority |
|---|---|---|---|
| R1 | **Wrong availability answer** (says free when taken, or the reverse) | Lost sale, broken trust at checkout | P0 |
| R2 | **Doors disagree** on the same name | Confusion, support tickets | P0 |
| R3 | **Bad input handling** (no TLD, `.com` vs `com`, invalid characters, length) | 500s, confusing errors | P0 |
| R4 | **Wrong or missing price / premium not flagged** | Revenue loss or surprise charge | P1 |
| R5 | **Search fails or hangs** | User drops off | P1 |
| R6 | **Suggestions are invalid or not actually available** | Weaker upsell, dead ends | P1 |
| R7 | **API contract drifts from the docs** (fields, enums, auth) | Integrators break | P1 |

## 3. Scope by door

### A. Public API (P0)
- **Check availability:** taken → `available: false`; random new name → `available: true`; response fields and
  types; case normalization.
- **Input validation:** missing TLD, unknown TLD, TLD Wix doesn't sell, empty, underscore, leading/trailing
  hyphen, non-Latin, 63/64-character boundary → clean 400 with a specific message, never a 500.
- **Suggest domains:** respects the limit, `count` matches the list, every result is a valid `name.tld`,
  the TLD filter works, `.com` (with dot) is rejected, and suggestions are really available.
- **Auth:** no key, bad key, missing account ID → expected 401/403 per the docs.
- **Docs vs. behavior:** enums (`premiumType`) and limits match what's documented.

### B. Domain storefront (P0)
- Taken name → "already registered" + alternatives. Free name → "Available now!" + price. **Stop before the cart.**
- Premium name → premium label and price. TLD Wix doesn't sell → clear message, not a false "available".
- Odd input: spaces, no TLD, emoji, very long names. Loading, empty and error states.

### C. Business Name Generator (P1)
- Keyword → names and domains appear. Domains shown as available really are (cross-check with the API).
- Odd input: one character, long phrase, non-Latin text.

### D. WHOIS lookup (P1)
- Registered domain → record shown (**redacted data is expected, not a bug**).
- Unregistered domain → clear "not registered". Invalid input → validation, not a crash.

### E. Cross-door consistency (P0)
The same name must get the **same availability and premium flag** at every door.
Allowed differences, not bugs: suggestions (generated), price/currency/TLDs by location, point-in-time changes.

## 4. Approach

| Layer | What | Why |
|---|---|---|
| **API automation (deep)** | Contract, validation, auth, suggestion validity | Fast, stable, cheap. The storefront calls the same `domain-search/v2` endpoints (seen in DevTools), so this covers the core logic behind the main door. |
| **UI automation (shallow)** | Storefront: taken vs. free, and UI-vs-API consistency | Real pages are slow and change often. Keep a few high-value flows with stable locators (`data-hook`, roles). |
| **Manual exploratory** | All web doors, UX, edge input, cross-door comparison, pricing | Needs judgment; not worth automating in 3 hours. |

**Test data.** Taken: `google.com`. Free: `qa-<random>.com` (practically never registered).
No hardcoded expectations for suggestions or prices.

## 5. Automated coverage today

| Area | Tests | Risks |
|---|---|---|
| `tests/api/test_check_availability.py` | Taken/free, fields, case, length boundary, 8 invalid inputs, TLD not sold, premiumType enum | R1, R3, R7 |
| `tests/api/test_suggest_domains.py` | Limit, count, valid domains, TLD filter, dot rejected, suggestions available | R6, R3 |
| `tests/api/test_authentication.py` | No key / no account ID / bad key | R7 |
| `tests/ui/test_storefront_search.py` | Taken message, available card, **storefront vs. API agree** | R1, R2 |

Known differences from the docs are tests marked `xfail(strict=True)`: they document the gap, and they start
failing (as a signal) if Wix changes the behavior. Details in `FINDINGS.md`.

## 6. Deliberately left out

| Left out | Why |
|---|---|
| Checkout, payment, purchases | Forbidden, and outside "can I get this name?" |
| Load / performance testing | Forbidden. I only note response times I see. |
| Exact prices, multiple locations | Prices change by design; I test from one location (Israel). Noted as a risk. |
| Cross-browser, mobile | Time-boxed: Chromium only. Next-week item. |
| Accessibility audit | Important but time-boxed; spot-check at most. |
| Exact suggestion content | Generated by design. I test the contract only. |
| Security beyond auth basics | Out of a 3-hour scope. |
| UI automation of Name Generator / WHOIS | Lower priority (P1); covered manually first. |

## 7. Assumptions and open questions
- I test from Israel: prices are in ₪ and `.co.il` appears in suggestions. Other locations are not covered.
- Is the anonymous API access intentional (a public endpoint used by the storefront) or an auth gap?
- How fresh is availability data, and is it cached differently per door?

## 8. Done means
All P0 areas checked, findings logged with evidence, API + storefront automation green with one command,
and known gaps written down here.
