# Report and persistent research

## Storage

Keep research in the active workspace, not in the installed skill:

```text
stock-research/<ISIN>/
  <YYYYMMDDTHHMMSS+offset>/
    report.md
    manifest.json
    financials.json
    calculation-inputs.json
    calculation-results.json
    sources/
```

Use a safe timestamp with seconds/timezone; add a suffix on collision. Never overwrite earlier runs. The manifest records issuer name, ISIN, exchange identifiers, quote exchange, timestamp/timezone, mode, deadline, ownership (held/not-held/unknown), recommended action (or conditional actions when ownership is unknown), action timing, coverage, gaps, complete/partial status and previous-run relative path. If ISIN is unverified, save an unresolved draft without merging companies or finalizing identity-dependent analysis.

The manifest source list assigns within-run source IDs with URL, title, publication date if known, retrieval timestamp, financial period, type, local extract path and extraction outcome. Quotes also record observation date/time and closing/intraday/delayed status. Unknown dates remain null. For decision-driving sources also record publisher/author, claim-specific authority, original versus mirror status, known commercial interests and verification/conflict status as described in sources.md.

In `financials.json`, separate source facts from derived metrics. Each fact records name/definition, value or null, unit, currency, period start/end, consolidated/standalone basis, source ID, document locator and reported/restated/derived status. Derived values reference inputs/formulas. Forecasts belong in calculation inputs, not reported facts. Record material conflicts and accounting choices.

Save consulted documents/relevant extracts, not bulk mirrors. Filenames identify document and period. No external database or paid service is needed.

For adaptive runs, store worker and reviewer artifacts under `agents/<task-id>/`. Add `manifest.json.orchestration` with route/experimental status, requested and runtime-confirmed model/reasoning settings, task IDs/roles/statuses, attempts, timestamps, artifact references, repair/review outcomes, unresolved blockers and available usage/tool counters. Unknown measurements remain null. The coordinator alone writes canonical records; prior reports without this optional field remain valid. Include review limitations and unresolved findings in the report without presenting model agreement as corroboration.

When native queue notifications are used, keep job/notification records with the run: run/task ID, parent session ID, result path, exit/timing data, notification attempt/outcome and consumed status. Include references in the manifest (under orchestration for adaptive runs). A queued message alone never marks research complete; inspect its underlying result. Preserve these records separately from investment evidence.

## Report order

1. **Action and mandate:** lead with Buy / Hold / Sell / Wait / Avoid buying / Insufficient evidence and ownership context. Immediately show horizon/deadline, action timing, supported entry/exit conditions, main reason and essential limitations. For unknown ownership, give separate prospective-buyer/existing-holder actions. Include issuer/exchange/ISIN, as-of time, price timestamp and latest financial period; separate business-quality, valuation, risk and confidence assessments.
2. **Business and thesis:** earnings drivers, competitive position, industry and capital allocation.
3. **Financial evidence:** five-year trends where available, latest results/comparisons, cash/debt and earnings-quality adjustments. Financial-sector reports use appropriate metrics.
4. **Governance and downside:** promoter/pledge changes, audit/related-party concerns, contingencies, refinancing and permanent-loss risks; distinguish allegations from facts.
5. **Peers and valuation:** relevant peers, current valuation, scenario inputs, price ranges and returns. Default includes years 3 and 5; one-year uses actual remaining deadline. Label present-value DCF separately.
6. **Assumption audit and bull/bear challenge:** include the driver table from investor-discipline.md, strongest evidence-backed objection, original-source/arithmetic recheck, unresolved issues and their effect on the action.
7. **Horizon-specific review:** long-term milestones or sourced 12-month catalysts with timing certainty, delay stress, exit conditions and deadline review.
8. **Changes since prior run:** facts, corrections/restatements, management delivery, forecasts, price/valuation, action, ownership and horizon changes. First run establishes baseline. Older reports may use Attractive/Watch/Avoid labels; preserve them and explain the transition to an explicit action without rewriting history.
9. **Sources and open questions:** direct document links and locators, gaps, calculation-file links and what could change the conclusion.

Cite material claims and tables near the evidence, linking actual documents with pages/sections. Derived metrics reference inputs/formulas. Explain missing values rather than fabricating tables. Use plain English, define abbreviations, and scale length to evidence without a fixed word quota or boilerplate disclaimer.

## Updates and failures

Read the latest complete or partial run for the **same ISIN**, retaining its status; partial data are not verified by reuse. Inherit its horizon on an ordinary update. Carry the original one-year deadline forward; if expired, provide a deadline review and request a new mandate before another forecast. Refresh quotes, new filings and announcements; reuse immutable old documents with original provenance.

Compare prior forecast assumptions with actual comparable outcomes where available, separating input errors, operating surprises, multiple changes and timing. Never rewrite old forecasts to match facts. Explain corrections separately from developments. When horizon changes, state that the verdicts answer different questions even if fundamentals are unchanged.

On retrieval/validation failure save a partial report with completed research, exact gaps, attempted sources, conclusions withheld and feasible next steps. Never write failed/stale data as verified or destroy earlier research.

## Final chat contract

Display the recommendation directly; a report link alone is insufficient. Use this compact structure, replacing every field with supported findings:

- **Action:** selected action and ownership context, or two conditional actions if ownership is unknown.
- **Horizon:** 3–5 years, or the explicit remaining period and exit deadline.
- **Timing and conditions:** act now or when a specified condition is met; model-supported entry/exit ranges and earlier thesis-invalidating conditions. Mark unavailable estimates clearly.
- **Why:** main evidence-based reason, confidence and any material limitation.
- **Report:** absolute link and complete/partial status.

Do not turn hypothetical scenario prices into guaranteed sale prices, fabricate an exact optimal sale date, or schedule/execute trades.
