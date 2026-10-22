# Indian Stock Analysis

A Codex skill for evidence-based NSE/BSE stock research, with long-term and one-year horizons, source verification, valuation scenarios, and ownership-aware Buy/Hold/Sell recommendations.

## What it does

- Evaluates business quality, financial performance, governance, capital allocation, and relevant peers using public evidence.
- Defaults to a **3–5-year horizon**, with scenarios for both years. Supports an explicit **exit within 12 months** and preserves the original deadline on updates.
- Leads reports with **Buy, Hold, Sell, Wait, Avoid buying, or Insufficient evidence**, followed by timing and conditions. Treats an existing purchase price separately from fair value.
- Prioritizes exchange filings, company reports, regulators, and credit-rating rationales. Uses Crawl4AI for retrieval and records source locations, periods, units, and accounting basis.
- Calculates conditional valuation scenarios and returns using a standard-library Python helper, with sector-specific treatment for banks and NBFCs.
- Saves dated research, source extracts, assumptions, and calculations in the active workspace for later comparison.

## Install

Requires Codex with local skills support, Python 3, and the Crawl4AI skill/CLI for the intended live-research workflow. Install Crawl4AI separately; it is not bundled here. The skill documents disclosed retrieval fallbacks when sources or tools are unavailable.

Clone into an unused skill directory:

```bash
git clone https://github.com/Rishabh060105/India-stock-analysis.git "${CODEX_HOME:-$HOME/.codex}/skills/india-stock-analysis"
```

Restart Codex to discover the skill. If that directory already exists, review and back it up before replacing it.

## Example prompts

```text
Use $india-stock-analysis to analyse Asian Paints for a 3–5-year investment.

Use $india-stock-analysis to analyse this NSE stock assuming I will sell
within one year. I am an existing holder; my average purchase price is ₹100.

Use $india-stock-analysis to update my previous analysis after the latest
results, keeping the original exit deadline.
```

## Execution and experimental orchestration

Ordinary requests use the invoking chat's single-agent workflow. An explicitly requested adaptive team uses a bounded, reusable pool: a GPT-5.6 Luna coordinator and combined research specialist at `max` reasoning, with a GPT-6 Astra reviewer at `medium`. Required models are never silently substituted.

**The adaptive team is experimental and has not passed its comparative acceptance gate.** It is not the default, and no efficiency or investment-performance advantage is claimed. See [orchestration](references/orchestration.md) for routing, model requirements, review limits, benchmark limitations, and native completion/queue guidance. End-to-end queue delivery remains unverified.

## Package and validation

[SKILL.md](SKILL.md) is the entrypoint. Methodology and source guidance live in `references/`; `scripts/calculate.py` provides reproducible calculations; `tests/` contains synthetic calculation fixtures and tests.

```bash
python3 -m unittest discover -s tests -v
```

See [validation cases](references/validation-cases.md) for behavioral checks. Passing calculation tests does not validate future returns or certify every research conclusion.

## Limits

Forecasts are conditional scenarios. Missing essential evidence blocks unsupported recommendations; stale quotes do not justify claims about today's price. Returns default to before taxes and transaction costs. The skill does not execute trades, allocate portfolios, or schedule monitoring.

Personal research reports and benchmark run artifacts are not included in this repository.
