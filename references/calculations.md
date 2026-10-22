# Calculation helper contract

`scripts/calculate.py` uses Python 3 standard library only. It accepts one JSON input file and writes JSON to stdout or a **new** `--output` path. Existing output files are never overwritten; errors exit with code 2. Rates/returns are decimal fractions (0.12 = 12%). The helper checks arithmetic and basic domains, not sources, assumptions, governance or investment suitability. `evidence_verified` is always false.

## Input

Required `analysis_date`: ISO `YYYY-MM-DD`, using the user-facing date. Optional fields:

- `sector`: `nonfinancial` (default), `bank`, `nbfc`, `insurer`.
- `horizon`: `{ "mode": "long-term" }` by default, or `{ "mode": "one-year", "exit_date": "2027-10-05" }`. An exit date without mode selects one-year. One-year without a deadline uses the next calendar anniversary. Long-term accepts no deadline. Preserve prior deadline explicitly on updates; the helper does not read history or parse natural language. Dates beyond 12 months are invalid for one-year mode; dates on/before analysis date return deadline-review and prohibit forecasts.
- `quote`: `{ "price_inr": 100, "date": "2026-10-05" }`; omit if unavailable. Observation time, exchange and evidence belong in the manifest. Calendar age does not verify market-session freshness. A stale quote can be calculated only for clearly dated conditional scenarios, never silently presented as current.
- `purchase`: `{ "price_inr": 80, "date": "2026-01-05", "dividends_received_inr": 2 }`. Date and received dividends are optional. Without received dividends only cost-basis **price** returns are available. Without acquisition date, no cost-basis annualization. Zero received dividends must be an explicit known value. Price and all dividends must use the same split/bonus-adjusted share basis; complex position cash flows require a separate cash-flow model.
- `financials`: array of records containing `period`, `period_months`, `currency` (INR), `unit` and `amounts`. Supported monetary units: `inr`, `thousand`, `lakh`, `million`, `crore`, `billion`. All amounts in a record share this unit. Supported metric inputs: `revenue`, `ebit`, `pat`, `cfo`, `capex` (positive outflow), `debt`, `cash`, `interest`, `equity_open`, `equity_close`, `capital_open`, `capital_close`. Use attributable common profit/equity for ROE. Basis/provenance remain in `financials.json`. Omitted/null inputs produce null dependent metrics; nonpositive ratio denominators and nonannual ROE/ROCE are unavailable. Bank/NBFC/insurer records get ROE and normalized amounts, without industrial cash-flow/leverage metrics. Additional sector metrics need explicit sourced calculations.
- `scenarios`: array using `name` bear/base/bull, `method`, `exit_multiple` as `[low, high]`, `diluted_shares_crore`, and `future_dividends_inr` for the entire remaining interval. Long-term needs `years` 3 or 5 per row (six rows total); one-year derives years from deadline (three rows, omit `years`). Each row's operating forecast and multiple rationale must be explained in the report. All share totals are in crore shares and monetary totals in INR crore, irrespective of financial-record units.

Methods:

| Method | Required scenario inputs | Price formula |
| --- | --- | --- |
| `pe` | `net_income_crore` > 0 attributable to common shareholders | net income × exit P/E / diluted shares |
| `pb` | `common_equity_crore` > 0 | common equity × exit P/B / diluted shares |
| `ev_ebitda` | `ebitda_crore` > 0; explicit nonnegative `debt_crore`, `cash_crore`, `other_claims_crore` | (EBITDA × exit multiple − debt + cash − other claims) / diluted shares |

Multiples and shares must be positive. EV/EBITDA is nonfinancial-only. Other claims include minorities and debt-like claims not already included in debt. Enter zero explicitly when verified absent. Negative implied equity is retained in output and flagged; common share value floors at zero, not a negative stock price. Explain any floor as a distress result.

Optional `dcf`: `fcff_crore` (array of annual year-end FCFF), decimal `discount_rate`, `terminal_growth`, nonnegative `debt_crore`, `cash_crore`, `other_claims_crore`, positive current `diluted_shares_crore`. Nonfinancial-only; rate must exceed growth, growth > −1, final FCFF > 0. Earlier negative FCFF is allowed. Output is **present** value with terminal-value contribution, not an exit price. Run sensitivity cases with changed inputs in distinct files; inputs passing mathematical checks still require economic justification.

## Example: synthetic bank, one-year exit

This is a calculator example, not real market data or an investment recommendation. For a complete report add bear and bull rows, source records, operating assumptions and governance analysis.

```json
{
  "analysis_date": "2026-10-05",
  "sector": "bank",
  "horizon": {"mode": "one-year", "exit_date": "2027-10-05"},
  "quote": {"price_inr": 100, "date": "2026-10-05"},
  "scenarios": [{
    "name": "base",
    "method": "pb",
    "common_equity_crore": 1000,
    "diluted_shares_crore": 10,
    "exit_multiple": [1.2, 1.4],
    "future_dividends_inr": 3
  }]
}
```

Expected exit range: INR 120–140; holding-period returns: 23%–43%. The helper flags the incomplete scenario set and cannot verify the quote. One-year annualization uses actual days / 365.25; long-term uses nominal years 3 and 5. Total returns assume cash dividends held without reinvestment and exclude taxes/costs; annualized figures are terminal-wealth rates, not IRRs. Use dates/cash-flow IRR separately if reinvestment or cash-flow timing matters.

`to_crore` and `cagr` are also importable helpers. CAGR returns null for nonpositive endpoints; it never reports a misleading growth rate across a sign change. The CLI does not automatically compute growth across financial records with possibly incompatible periods/bases.
