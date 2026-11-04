# Findings

**Tested:** 2026-11-04 · Chromium (Playwright + in-app browser) · from Israel (₪, browser language Hebrew) · logged out

**Rating:** *Severity* = impact on the user or business if it happens. *Priority* = how soon I'd fix it.

| # | Finding | Door | Severity | Priority |
|---|---|---|---|---|
| F1 | Public API doesn't enforce authentication | API | Medium | **High** |
| F2 | A search made right after page load is silently ignored | Storefront | Medium | Medium |
| F3 | Length-limit message is off by one and contradicts its own suggestions | Storefront | Low | Medium |
| F4 | Key pricing terms only in a hover tooltip, behind a misleading crossed-out price | Storefront, Generator | Medium | Medium |
| F5 | Suggestions take 2–5 s, so the page looks stuck after the answer is known | Storefront | Low | Low |

---

## F1. Public API doesn't enforce authentication
**Severity: Medium · Priority: High**

**Steps**
```
GET https://www.wixapis.com/domain-search/v2/check-domain-availability?domain=google.com
```
(a) with no headers · (b) with `Authorization: not-a-real-key` · (c) with a real key but no `wix-account-id`

**Expected:** 401 or 403. The docs say: *"This call requires an account level API key."*

**Actual:** 200 with full data in all three cases:
```json
{"availability":{"domain":"google.com","available":false,"premium":false,"premiumType":"UNKNOWN_PREMIUM_TYPE"}}
```
`suggest-domains` behaves the same way.

**Evidence:** `tests/api/test_authentication.py`, 4 tests marked `xfail(strict=True)`. They start failing if auth gets enforced.

**Why this rating:** Severity is not High because the data is public anyway (the WHOIS door shows it) and nothing
private leaks. Priority is High because, without a key, there's no per-account rate limit or attribution, which
makes anonymous scraping easy. Also, either the docs or the gateway is wrong, and integrators build on the docs.

---

## F2. A search made right after page load is silently ignored
**Severity: Medium · Priority: Medium**

**Steps**
1. Open https://www.wix.com/domains.
2. As soon as the page fires `load`, type `google.com` in the hero search box and click **Search Domains**.

**Expected:** navigates to `/domain/result/?q=google.com`.

**Actual:** nothing happens. There's no navigation, no error and no message. The text stays in the box.
Searching again a few seconds later works.

**Evidence** (headless Chromium, Playwright):
| Wait before searching | First search |
|---|---|
| `load` (Playwright default) | ignored in **5/5** runs; the second try always worked |
| `load`, then `fill()` | ignored in 1 of 2 runs (an earlier probe) |
| `networkidle` (~4.7 s after navigation) | worked in **3/3** runs |

Fix in the test code: `DomainsHomePage.open()` waits for `networkidle` (`src/pages/domains_home_page.py`).

**Why this rating:** it's the main entry point of the main door, and the failure is silent, so the user doesn't know
to retry. **Caveat:** I couldn't reproduce it by hand at normal typing speed, so real-user impact is not proven.
It's most likely for fast users on slow devices or networks, hence Medium priority.

---

## F3. Length-limit message is off by one and contradicts its own suggestions
**Severity: Low · Priority: Medium**

**Steps:** search a 64-character name plus `.com`:
`https://www.wix.com/domain/result/?q=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.com`

**Expected:** a message matching the real rule, *63 characters or fewer, not counting the TLD*.

**Actual:**
- The message says: *"Domains should contain **fewer than 63** characters."* (that would mean 62 at most)
- The page's own "Best Match" suggestions are **63** characters long (`aaa…a.biz`, `.info`, `.store`; counted with JS: 63, 63, 63).
- The API accepts exactly 63: `test_63_character_name_is_accepted` passes. 64 returns `DOMAIN_TOO_LONG`.

**Why this rating:** low severity, because it's an edge case and the user still gets options. Medium priority,
because it's a one-word fix ("63 or fewer") and the page visibly contradicts itself, which hurts trust.

---

## F4. Key pricing terms only in a hover tooltip, behind a misleading crossed-out price
**Severity: Medium · Priority: Medium** · *UX/trust risk, not a functional bug*

**Steps:** search `google.com`. Look at a `.biz` suggestion card, then hover the ⓘ icon. Repeat for `.ai`.

**Actual:**
| TLD | Card shows | Only in the tooltip |
|---|---|---|
| `.biz` | ~~₪27.44/yr~~ **₪0.00/yr** · Free for 1 year | "free for one year **with any annual plan**. **Renews at ₪124.73**" |
| `.ai` | ~~₪563.80/yr~~ **₪362.07/yr** · Intro offer | "Renews at ₪563.80. **.ai domains can only be purchased for 2+ year cycles.**" |

The price service response agrees with the tooltip (`suggested-tld-display-prices`):
```json
{"tld":"biz","pricing":{"price":"₪0.00","originalPrice":"₪27.44","pricingStrategy":"FREE_FIRST_YEAR","renewalPrice":"₪124.73"}}
```
The same pattern applies to `.com` (₪21.47 crossed out, renews at ₪90.19) and `.online` (₪23.97, renews at ₪142.10).

**Why this rating:** the terms *are* disclosed, so this is not hidden pricing, and the final price shows before
payment, so no one is charged wrongly. But the crossed-out price reads as "the normal price" when the real ongoing
price is up to 4.5× higher, and the ₪0.00 depends on buying a site plan. Hover-only disclosure is also weak on touch
devices (not tested). That combination makes it a trust and conversion risk on the money path.

**Correction:** I first read the network data alone and thought the renewal price was hidden.
Checking the actual UI showed the tooltip, so I downgraded this from "hidden price" to "disclosed only on hover".

---

## F5. Suggestions take 2–5 s, so the page looks stuck after the answer is known
**Severity: Low · Priority: Low**

**Evidence** (browser Resource Timing, same page loads):
| Search | `check-domain-availability` | `suggest-domains` |
|---|---|---|
| `google.com` | 393 ms | **5,178 ms** |
| `qa-yuval-2026.com` | 418 ms | 2,234 ms |
| `sunnybaker` | (not called) | 1,828 ms |

During manual testing, the tester saw grey placeholders and reported that the page was "stuck".

**Why this rating:** results do arrive, so this is Low/Low. But it's a cheap UX win: the availability answer is
ready in about 0.4 s and could be shown before the suggestions finish loading.
*(Observed timings from a handful of searches, not a load test.)*

---

## Observations (real, but below the top 5)
- **Inconsistent input normalization:** for `  Google.COM  `, the availability call gets `google.com`, but
  `suggest-domains` and the on-screen message get the raw text.
- **`premiumType: UNKNOWN_PREMIUM_TYPE`** isn't in the documented list of values. It appears only when `premium: false`,
  so it's a docs gap (strict-xfail test in `test_check_availability.py`).
- **Docs say the domain is "max 63 characters"**, but the API applies 63 to the name only, without the TLD.
- **The storefront sends `suggest-domains` a query with the TLD** (`query=google.com`), which the docs say it must not.
- **Console noise for logged-out users on every search:** 401 from `user-domains`,
  `Uncaught (in promise) SyntaxError: Unexpected token '<'`, and `EmptyCartError` ×6.
- **Suggestions include trademarks** (`getgoogle.biz`, `googlecompany.net`). This is a legal risk, not a functional bug.
- **WHOIS → storefront redirect** calls `check-domain-availability` twice for the same name.

## Not findings (expected behavior)
- WHOIS contact data is redacted.
- `.co.il` is offered and often ranked "Best Match" for a visitor in Israel.
- A TLD Wix doesn't sell (`.gov`) is rejected with a clear message.
- Raw non-Latin input is rejected by the API; the storefront converts it to punycode first.
