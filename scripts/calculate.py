#!/usr/bin/env python3
"""Deterministic arithmetic only: no fetching, stock scoring, or trading."""
import argparse
import json
import math
import sys
from datetime import date
from pathlib import Path


def number(value, label, *, minimum=None, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{label} must be a finite number")
    if not math.isfinite(value):
        raise ValueError(f"{label} must be finite")
    if positive and value <= 0:
        raise ValueError(f"{label} must be positive")
    if minimum is not None and value < minimum:
        raise ValueError(f"{label} must be >= {minimum}")
    return float(value)


def field(data, key, **kwargs):
    if key not in data:
        raise ValueError(f"Missing required field: {key}")
    return number(data[key], key, **kwargs)


def parse_date(value, label):
    if not isinstance(value, str):
        raise ValueError(f"{label} must be YYYY-MM-DD")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be YYYY-MM-DD") from exc
    if parsed.isoformat() != value:
        raise ValueError(f"{label} must be YYYY-MM-DD")
    return parsed


def anniversary(day, years=1):
    try:
        return day.replace(year=day.year + years)
    except ValueError:
        return day.replace(year=day.year + years, day=28)


def horizon(analysis_date, settings=None):
    """Caller carries prior settings/deadline forward on updates."""
    today = parse_date(analysis_date, "analysis_date")
    settings = {} if settings is None else settings
    mode = settings.get("mode", "one-year" if settings.get("exit_date") else "long-term")
    if mode == "long-term":
        if settings.get("exit_date") is not None:
            raise ValueError("long-term mode cannot have an exit_date")
        return {"mode": mode, "forecast_years": [3, 5], "status": "active"}
    if mode != "one-year":
        raise ValueError("mode must be long-term or one-year")
    deadline = parse_date(settings["exit_date"], "exit_date") if settings.get("exit_date") else anniversary(today)
    if deadline > anniversary(today):
        raise ValueError("one-year exit_date cannot exceed 12 calendar months")
    days = (deadline - today).days
    return {"mode": mode, "exit_date": deadline.isoformat(), "remaining_days": days,
            "forecast_years": [days / 365.25] if days > 0 else [],
            "status": "active" if days > 0 else "deadline-review"}


def to_crore(value, unit):
    factors = {"inr": 1e-7, "thousand": 1e-4, "lakh": 0.01,
               "million": 0.1, "crore": 1.0, "billion": 100.0}
    if unit not in factors:
        raise ValueError(f"Unsupported INR unit: {unit}")
    return number(value, "amount") * factors[unit]


def cagr(start, end, years):
    start, end = number(start, "start"), number(end, "end")
    years = number(years, "years", positive=True)
    return (end / start) ** (1 / years) - 1 if start > 0 and end > 0 else None


def metrics(record, sector):
    if record.get("currency", "INR") != "INR":
        raise ValueError("Convert and document non-INR financials before calculation")
    amounts = {}
    for key, value in record.get("amounts", {}).items():
        amounts[key] = None if value is None else to_crore(value, record.get("unit", "crore"))

    def ratio(a, b):
        x, y = amounts.get(a), amounts.get(b)
        return x / y if x is not None and y is not None and y > 0 else None

    def difference(a, b):
        x, y = amounts.get(a), amounts.get(b)
        return x - y if x is not None and y is not None else None

    def average_return(profit, opening, closing):
        p, a, b = amounts.get(profit), amounts.get(opening), amounts.get(closing)
        if record.get("period_months") != 12 or p is None or a is None or b is None or min(a, b) <= 0:
            return None
        return p / ((a + b) / 2)

    result = {"period": record.get("period"), "amounts_inr_crore": amounts,
              "roe": average_return("pat", "equity_open", "equity_close")}
    if sector == "nonfinancial":
        if amounts.get("capex") is not None and amounts["capex"] < 0:
            raise ValueError("capex must be entered as a positive cash outflow")
        result.update({"ebit_margin": ratio("ebit", "revenue"), "pat_margin": ratio("pat", "revenue"),
                       "cash_conversion": ratio("cfo", "pat"),
                       "cfo_less_capex_crore": difference("cfo", "capex"),
                       "net_debt_crore": difference("debt", "cash"),
                       "interest_cover": ratio("ebit", "interest"),
                       "roce": average_return("ebit", "capital_open", "capital_close")})
    return result


def returns(entry, exit_price, dividends, years):
    entry = number(entry, "entry_price", positive=True)
    exit_price = number(exit_price, "exit_price", minimum=0)
    dividends = number(dividends, "dividends", minimum=0)
    years = number(years, "years", positive=True)
    wealth = (exit_price + dividends) / entry
    return {"holding_period_return": wealth - 1, "annualized_terminal_wealth_return": wealth ** (1 / years) - 1}


def exit_range(scenario, sector):
    method = scenario.get("method")
    if method not in {"pe", "pb", "ev_ebitda"}:
        raise ValueError("method must be pe, pb, or ev_ebitda")
    if method == "ev_ebitda" and sector != "nonfinancial":
        raise ValueError("Industrial EV/EBITDA is unsupported for financial-sector companies")
    multiples = scenario.get("exit_multiple")
    if not isinstance(multiples, list) or len(multiples) != 2:
        raise ValueError("exit_multiple must be [low, high]")
    low, high = [number(x, "exit_multiple", positive=True) for x in multiples]
    if low > high:
        raise ValueError("exit_multiple low exceeds high")
    shares = field(scenario, "diluted_shares_crore", positive=True)
    equity_adjustment = 0.0
    if method == "pe":
        driver = field(scenario, "net_income_crore", positive=True)
    elif method == "pb":
        driver = field(scenario, "common_equity_crore", positive=True)
    else:
        driver = field(scenario, "ebitda_crore", positive=True)
        equity_adjustment = (field(scenario, "cash_crore", minimum=0)
                             - field(scenario, "debt_crore", minimum=0)
                             - field(scenario, "other_claims_crore", minimum=0))
    equity = [driver * multiple + equity_adjustment for multiple in (low, high)]
    return {"exit_price_inr": [max(0, x) / shares for x in equity],
            "equity_value_crore": equity,
            "equity_floor_applied": any(x < 0 for x in equity)}


def dcf(data, sector):
    if sector != "nonfinancial":
        raise ValueError("FCFF DCF is unsupported for financial-sector companies; use an equity model")
    flows = data.get("fcff_crore")
    if not isinstance(flows, list) or not flows:
        raise ValueError("fcff_crore must contain explicit year-end cash flows")
    flows = [number(x, "fcff") for x in flows]
    rate = field(data, "discount_rate", positive=True)
    growth = field(data, "terminal_growth")
    if growth <= -1 or rate <= growth or flows[-1] <= 0:
        raise ValueError("DCF needs discount_rate > terminal_growth > -1 and positive final FCFF")
    terminal = flows[-1] * (1 + growth) / (rate - growth)
    terminal_pv = terminal / (1 + rate) ** len(flows)
    enterprise = sum(x / (1 + rate) ** (i + 1) for i, x in enumerate(flows)) + terminal_pv
    equity = (enterprise - field(data, "debt_crore", minimum=0) + field(data, "cash_crore", minimum=0)
              - field(data, "other_claims_crore", minimum=0))
    shares = field(data, "diluted_shares_crore", positive=True)
    return {"enterprise_value_crore": enterprise, "common_equity_value_crore": equity,
            "present_value_per_share_inr": max(0, equity) / shares,
            "equity_floor_applied": equity < 0,
            "terminal_pv_fraction": terminal_pv / enterprise if enterprise > 0 else None}


def calculate(data):
    analysis_day = parse_date(data.get("analysis_date"), "analysis_date")
    window = horizon(data["analysis_date"], data.get("horizon"))
    sector = data.get("sector", "nonfinancial")
    if sector not in {"nonfinancial", "bank", "nbfc", "insurer"}:
        raise ValueError("sector must be nonfinancial, bank, nbfc, or insurer")
    result = {"analysis_date": analysis_day.isoformat(), "horizon": window,
              "sector": sector, "rates_are_decimals": True,
              "evidence_verified": False, "warnings": [],
              "metrics": [metrics(row, sector) for row in data.get("financials", [])], "scenarios": []}
    quote = data.get("quote")
    if quote is not None:
        entry = field(quote, "price_inr", positive=True)
        quote_date = parse_date(quote.get("date"), "quote.date")
        if quote_date > analysis_day:
            raise ValueError("Quote date cannot be after analysis_date")
        result["quote_age_calendar_days"] = (analysis_day - quote_date).days
        result["warnings"].append("Verify quote provenance and latest trading session; calendar age alone does not establish freshness.")
    else:
        entry = None
        result["warnings"].append("No quote: only conditional valuations; current-price returns and attractiveness are unavailable.")
    purchase = data.get("purchase")
    purchase_entry, received, acquired = None, None, None
    if purchase is not None:
        purchase_entry = field(purchase, "price_inr", positive=True)
        received = purchase.get("dividends_received_inr")
        if received is not None:
            received = number(received, "dividends_received_inr", minimum=0)
        if purchase.get("date"):
            acquired = parse_date(purchase["date"], "purchase.date")
            if acquired > analysis_day:
                raise ValueError("purchase.date cannot be after analysis_date")
        if received is None:
            result["warnings"].append("Past dividends unknown: cost-basis price return only; no since-purchase total return.")
    if window["status"] == "deadline-review":
        if data.get("scenarios") or data.get("dcf"):
            raise ValueError("Deadline reached: review exit mandate before making new forecasts")
        result["warnings"].append("Original exit deadline reached; do not automatically extend it.")
        return result
    seen = set()
    for scenario in data.get("scenarios", []):
        name = scenario.get("name")
        if name not in {"bear", "base", "bull"}:
            raise ValueError("scenario name must be bear, base, or bull")
        if window["mode"] == "long-term":
            years = field(scenario, "years", positive=True)
            if years not in (3, 5):
                raise ValueError("long-term scenarios must use 3 or 5 years")
            exit_day = anniversary(analysis_day, int(years))
        else:
            if "years" in scenario:
                raise ValueError("one-year scenario years are derived from exit_date; omit years")
            years = window["forecast_years"][0]
            exit_day = parse_date(window["exit_date"], "exit_date")
        key = (name, years)
        if key in seen:
            raise ValueError("Duplicate scenario name/horizon")
        seen.add(key)
        dividends = field(scenario, "future_dividends_inr", minimum=0)
        row = {"name": name, "years": years, "exit_date": exit_day.isoformat(), "method": scenario.get("method"),
               "future_dividends_inr": dividends, **exit_range(scenario, sector)}
        row["returns_from_quote"] = [returns(entry, p, dividends, years) for p in row["exit_price_inr"]] if entry else None
        if purchase_entry:
            row["cost_basis_price_return"] = [p / purchase_entry - 1 for p in row["exit_price_inr"]]
            row["cost_basis_total_return"] = None if received is None else [(p + dividends + received) / purchase_entry - 1 for p in row["exit_price_inr"]]
            if acquired is not None and received is not None:
                elapsed = (exit_day - acquired).days / 365.25
                row["cost_basis_annualized_return"] = [returns(purchase_entry, p, dividends + received, elapsed)["annualized_terminal_wealth_return"] for p in row["exit_price_inr"]]
        result["scenarios"].append(row)
    required = {(name, years) for name in ("bear", "base", "bull") for years in window["forecast_years"]}
    result["scenario_set_complete"] = seen == required
    if not result["scenario_set_complete"]:
        result["warnings"].append("Incomplete bear/base/bull set for the selected horizon(s); report must disclose missing scenarios.")
    if data.get("dcf") is not None:
        result["dcf"] = dcf(data["dcf"], sector)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, help="New output file; refuses to overwrite")
    args = parser.parse_args()
    try:
        result = calculate(json.loads(args.input.read_text(encoding="utf-8")))
        rendered = json.dumps(result, indent=2, allow_nan=False) + "\n"
        if args.output:
            with args.output.open("x", encoding="utf-8") as handle:
                handle.write(rendered)
        else:
            print(rendered, end="")
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError, OSError) as exc:
        print(f"Calculation failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
