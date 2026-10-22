# Sources and retrieval

## Priority by claim

| Need | First source | Supporting sources |
| --- | --- | --- |
| Identity, corporate actions, quote | NSE/BSE security page and dated disclosures | Company investor relations; dated public market-data service |
| Financials and notes | Audited consolidated annual report and filed results | Earlier filings, presentations; Screener for discovery/checks |
| Ownership, pledges, related parties, governance | NSE/BSE disclosures, annual-report notes | SEBI orders; attributed company explanations |
| Management claims and execution | Company/exchange-hosted transcripts, presentations, announcements | Accessible transcripts checked against official releases |
| Debt, liquidity, rating changes | Filings and actual CRISIL/ICRA/CARE rationales | Public lender/regulator material; credit opinions are not equity recommendations |
| Sector conditions and regulation | RBI/SEBI, sector regulator, official industry statistics | Public research and established financial journalism |

Company publications establish reported results and management statements, not independent proof of promotional claims. Two mirrors of a filing are one source. Distinguish news allegations, company responses and regulator findings.

Starting points (discover actual document links rather than guessing URLs):

- [SEBI filing directory](https://www.sebi.gov.in/curation/corporate_filings.html)
- [NSE annual reports](https://www.nseindia.com/companies-listing/corporate-filings-annual-reports)
- [NSE financial results](https://www.nseindia.com/companies-listing/corporate-filings-financial-results)
- [NSE shareholding patterns](https://www.nseindia.com/companies-listing/corporate-filings-shareholding-pattern)
- [BSE corporate filings](https://www.bseindia.com/corporates.html)
- [SEBI](https://www.sebi.gov.in/) and [RBI](https://www.rbi.org.in/)
- [CRISIL rationales](https://www.crisilratings.com/en/home/our-business/ratings/rating-rationale.html), [ICRA](https://www.icra.in/), [CARE Ratings](https://www.careratings.com/)
- [Screener](https://www.screener.in/) for financial history and document discovery; verify dates, definitions and original filings.

## Crawl4AI

Use the installed `crawl4ai:crawl4ai` skill when available. Find `crwl` on PATH, then try `~/.local/bin/crwl`; do not hard-code a user's home. Read `crwl --help` before advanced options. Ordinary Markdown extraction requires no LLM provider or paid key.

Every live coordinator, research specialist and reviewer prompt explicitly requires reading and using the Crawl4AI skill. For discovery, crawl accessible public search-result pages, then retrieve the original documents. Crawl4AI has no built-in search index: if a search page blocks extraction, use an available search tool for URL discovery and Crawl4AI for the underlying pages. Disclose any retrieval fallback; never claim a fallback was a Crawl4AI result. Frozen/offline validation uses its supplied documents without live searches.

```bash
crwl 'https://www.sebi.gov.in/curation/corporate_filings.html' -o markdown -O '<run-directory>/sources/sebi-filings.md'
crwl '<verified-company-investor-relations-url>' --deep-crawl bfs --max-pages 10 -o markdown -O '<run-directory>/sources/ir-discovery.md'
```

Replace placeholders, quote arguments safely, and save only inside the current run. Prefer individual documents after discovery. Verify issuer, dates, title and substantive content: exit code zero/HTTP 200 does not prove extraction succeeded. Login/challenge pages or empty JS shells are not evidence. For Python extraction check `result.success` and content.

On transient errors make one reasonable retry, then try the company/exchange mirror or another public retrieval tool and disclose which succeeded. Do not bypass authentication, access controls or paywalls. Cache/browser errors are local failures, not missing company disclosures. If Crawl4AI is unavailable, state the limitation and use available public read tools while retaining provenance. Do not install dependencies or create paid accounts silently.

For PDFs retain original URL and file. Extract selectable text with available PDF tools; visually verify column alignment, signs, units and period headings on pages supplying key figures. OCR/poorly aligned tables require visual verification; leave unverified values unavailable. Record PDF page numbers and printed labels if different. Inspect HTML images containing financial figures as well.

## Validate the source itself

For each decision-driving source, record publisher/author where known, document identity and original host, authority for the specific claim, publication/as-of date, financial period, locator, conflicts of interest and extraction/verification status. Verify an official document through its issuer/exchange/regulator directory when identity is uncertain; a familiar-looking URL alone is insufficient. Audit opinions have a scope and date; they do not certify every management forecast. Credit opinions assess credit risk, not stock upside. Unknown authorship or dates stay unknown.

Trace syndicated stories and mirrors to the originating disclosure; multiple copies do not independently corroborate it. Seek independent evidence for claims about market share, competitors and industry demand. Separate confirmed regulatory findings from allegations. Exclude crawler boilerplate, generated related answers and advertisements. For historical/as-of analysis, exclude documents published after the cutoff even if their reporting period precedes it. Record later corrections separately rather than leaking hindsight into the original forecast.

## Freshness and completeness

- Record quote time/timezone, exchange, closing/intraday/delayed status and retrieval time. Verify the latest completed trading session, including holidays. A cached 'current price' label is insufficient.
- Check freshness of results, annual reports, ownership disclosures and subsequent announcements independently of the quote.
- Match quarterly comparisons for seasonality. Do not add overlapping year-to-date values as quarters. Q4 derived from annual minus nine-month results must be labelled derived.
- Prefer corrected/restated filings for calculations but preserve original data when explaining changes. Record the superseded source and reason.
- Resolve conflicts by checking basis, units, periods, attributable profit, share count and restatements. Explain material unresolved differences and withhold dependent conclusions.

## Design sources

The [user-provided Reddit discussion](https://www.reddit.com/r/ValueInvesting/comments/1v4o1h0/how_are_people_actually_using_ai_for_stock/) motivated traceable inputs, consistent definitions, bull/bear challenge and persistent research. It is not stock evidence; its promoted products are not dependencies.

[CFA Institute reporting-quality guidance](https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/evaluating-quality-financial-reports) informs sustainable-earnings, accounting and cash-flow checks. [NYU Stern financial-service value drivers](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/littlebook/bankvaluedriver.htm) informs ROE, capital reinvestment and equity valuation. These pages and the SEBI directory were reviewed during design on 2026-10-05; actual stock research must retrieve current evidence.
