"""Synthetic analytical fixtures; no live prices or investment-performance claims."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("calculate", ROOT / "scripts" / "calculate.py")
calc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calc)


def fixture(name):
    return json.loads((ROOT / "tests" / "fixtures" / f"{name}.json").read_text())


class Horizons(unittest.TestCase):
    def test_default_and_explicit_one_year(self):
        self.assertEqual(calc.horizon("2026-10-05")["forecast_years"], [3, 5])
        self.assertEqual(calc.horizon("2026-10-05", {"mode": "one-year"})["exit_date"], "2027-10-05")

    def test_deadline_without_mode_and_leap_anniversary(self):
        h = calc.horizon("2026-10-05", {"exit_date": "2027-03-31"})
        self.assertEqual(h["mode"], "one-year")
        self.assertEqual(h["remaining_days"], 177)
        self.assertEqual(calc.horizon("2024-02-29", {"mode": "one-year"})["exit_date"], "2025-02-28")

    def test_update_preserves_deadline_and_reduces_remaining_time(self):
        first = calc.calculate(fixture("bank"))
        update = fixture("bank")
        update["analysis_date"] = "2027-04-05"
        update["quote"]["date"] = "2027-04-05"
        later = calc.calculate(update)
        self.assertEqual(later["horizon"]["exit_date"], first["horizon"]["exit_date"])
        self.assertEqual(later["horizon"]["remaining_days"], 183)
        self.assertAlmostEqual(later["scenarios"][1]["returns_from_quote"][0]["holding_period_return"], 0.23)

    def test_expired_deadline_requires_review(self):
        for day in ("2027-10-05", "2027-10-06"):
            data = fixture("bank")
            data["analysis_date"] = day
            with self.assertRaises(ValueError):
                calc.calculate(data)
            data.pop("scenarios")
            self.assertEqual(calc.calculate(data)["horizon"]["status"], "deadline-review")

    def test_incompatible_or_excessive_deadlines(self):
        for settings in ({"mode": "long-term", "exit_date": "2027-01-01"},
                         {"mode": "one-year", "exit_date": "2027-10-06"}, {"mode": "two-year"}):
            with self.assertRaises(ValueError):
                calc.horizon("2026-10-05", settings)

    def test_horizon_switch_requires_matching_scenario_periods(self):
        data = fixture("nonfinancial")
        data["horizon"] = {"mode": "one-year"}
        with self.assertRaises(ValueError):
            calc.calculate(data)


class Financials(unittest.TestCase):
    def test_independent_unit_conversions(self):
        self.assertAlmostEqual(calc.to_crore(10000000, "inr"), 1)
        self.assertAlmostEqual(calc.to_crore(100, "lakh"), 1)
        self.assertAlmostEqual(calc.to_crore(10, "million"), 1)
        self.assertAlmostEqual(calc.to_crore(1, "billion"), 100)
        with self.assertRaises(ValueError):
            calc.to_crore(1, "usd")

    def test_profitable_nonfinancial_metrics(self):
        m = calc.calculate(fixture("nonfinancial"))["metrics"][0]
        self.assertEqual(m["amounts_inr_crore"]["revenue"], 1000)
        self.assertAlmostEqual(m["roe"], 0.2)
        self.assertAlmostEqual(m["roce"], 0.2)
        self.assertAlmostEqual(m["cash_conversion"], 1.5)
        self.assertEqual(m["cfo_less_capex_crore"], 120)
        self.assertEqual(m["net_debt_crore"], 200)
        self.assertEqual(m["interest_cover"], 10)

    def test_bank_roe_without_industrial_metrics(self):
        m = calc.calculate(fixture("bank"))["metrics"][0]
        self.assertAlmostEqual(m["roe"], 0.15)
        self.assertNotIn("cash_conversion", m)
        self.assertNotIn("cfo_less_capex_crore", m)
        self.assertNotIn("net_debt_crore", m)

    def test_missing_data_are_not_zero(self):
        output = calc.calculate(fixture("incomplete"))
        m = output["metrics"][0]
        self.assertIsNone(m["cash_conversion"])
        self.assertIsNone(m["cfo_less_capex_crore"])
        self.assertIsNone(m["net_debt_crore"])
        self.assertFalse(output["scenario_set_complete"])
        self.assertFalse(output["evidence_verified"])
        self.assertNotIn("verdict", output)

    def test_negative_profit_and_quarterly_roe(self):
        rec = {"period_months": 3, "amounts": {"pat": -2, "cfo": 4, "equity_open": 10, "equity_close": 10}}
        m = calc.metrics(rec, "nonfinancial")
        self.assertIsNone(m["roe"])
        self.assertIsNone(m["cash_conversion"])

    def test_cagr_and_invalid_endpoints(self):
        self.assertAlmostEqual(calc.cagr(100, 121, 2), 0.1)
        for start, end in ((-10, 10), (0, 10), (10, -10)):
            self.assertIsNone(calc.cagr(start, end, 3))
        with self.assertRaises(ValueError):
            calc.cagr(100, 110, 0)

    def test_nan_bool_currency_and_negative_capex_rejected(self):
        for bad in (float("nan"), float("inf"), True, "100"):
            with self.assertRaises(ValueError):
                calc.number(bad, "test")
        for rec in ({"currency": "USD"}, {"amounts": {"capex": -4}}):
            with self.assertRaises(ValueError):
                calc.metrics(rec, "nonfinancial")


class Valuations(unittest.TestCase):
    def test_complete_sets_and_dilution(self):
        result = calc.calculate(fixture("nonfinancial"))
        self.assertTrue(result["scenario_set_complete"])
        base = result["scenarios"][1]
        self.assertEqual(base["exit_price_inr"], [110, 132])
        self.assertAlmostEqual(base["returns_from_quote"][0]["holding_period_return"], 0.14)
        self.assertAlmostEqual(base["returns_from_quote"][1]["holding_period_return"], 0.36)
        self.assertAlmostEqual(base["returns_from_quote"][0]["annualized_terminal_wealth_return"], 1.14 ** (1 / 3) - 1)

    def test_bank_price_to_book(self):
        result = calc.calculate(fixture("bank"))
        self.assertTrue(result["scenario_set_complete"])
        base = result["scenarios"][1]
        self.assertEqual(base["exit_price_inr"], [120, 140])
        self.assertAlmostEqual(base["returns_from_quote"][0]["holding_period_return"], 0.23)
        self.assertAlmostEqual(base["returns_from_quote"][1]["holding_period_return"], 0.43)

    def test_catalyst_delay_is_changed_forecast_not_automatic_rerating(self):
        data = fixture("bank")
        data["scenarios"][1]["exit_multiple"] = [0.8, 1.0]
        base = calc.calculate(data)["scenarios"][1]
        self.assertEqual(base["exit_price_inr"], [80, 100])
        self.assertAlmostEqual(base["returns_from_quote"][0]["holding_period_return"], -0.17)
        self.assertEqual(base["exit_date"], "2027-10-05")

    def test_ev_bridge_and_distress_floor(self):
        s = {"method": "ev_ebitda", "ebitda_crore": 100, "exit_multiple": [8, 10],
             "debt_crore": 300, "cash_crore": 50, "other_claims_crore": 50, "diluted_shares_crore": 10}
        self.assertEqual(calc.exit_range(s, "nonfinancial")["exit_price_inr"], [50, 70])
        s["debt_crore"] = 1000
        result = calc.exit_range(s, "nonfinancial")
        self.assertEqual(result["exit_price_inr"], [0, 0])
        self.assertTrue(result["equity_floor_applied"])
        with self.assertRaises(ValueError):
            calc.exit_range(s, "bank")

    def test_invalid_scenarios(self):
        for key, value in (("net_income_crore", -10), ("diluted_shares_crore", 0), ("exit_multiple", [20, 10]),
                           ("future_dividends_inr", -1)):
            data = fixture("nonfinancial")
            data["scenarios"][0][key] = value
            with self.assertRaises(ValueError):
                calc.calculate(data)
        data = fixture("bank")
        data["scenarios"].append(copy.deepcopy(data["scenarios"][0]))
        with self.assertRaises(ValueError):
            calc.calculate(data)

    def test_missing_quote_and_stale_quote_are_not_certified(self):
        data = fixture("bank")
        data.pop("quote")
        result = calc.calculate(data)
        self.assertIsNone(result["scenarios"][0]["returns_from_quote"])
        data["quote"] = {"price_inr": 100, "date": "2026-09-01"}
        result = calc.calculate(data)
        self.assertEqual(result["quote_age_calendar_days"], 34)
        self.assertFalse(result["evidence_verified"])
        self.assertTrue(result["warnings"])
        data["quote"]["date"] = "2026-10-06"
        with self.assertRaises(ValueError):
            calc.calculate(data)

    def test_cost_basis_separate_from_valuation_and_current_returns(self):
        data = fixture("bank")
        before = calc.calculate(data)["scenarios"][1]
        data["purchase"] = {"price_inr": 80, "dividends_received_inr": 2}
        after = calc.calculate(data)["scenarios"][1]
        self.assertEqual(after["exit_price_inr"], before["exit_price_inr"])
        self.assertEqual(after["returns_from_quote"], before["returns_from_quote"])
        self.assertAlmostEqual(after["cost_basis_total_return"][0], 0.5625)
        self.assertNotIn("cost_basis_annualized_return", after)
        data["purchase"].pop("dividends_received_inr")
        after = calc.calculate(data)["scenarios"][1]
        self.assertIsNone(after["cost_basis_total_return"])
        self.assertAlmostEqual(after["cost_basis_price_return"][0], 0.5)

    def test_total_loss_and_dividend_only_return(self):
        self.assertEqual(calc.returns(100, 0, 0, 1)["holding_period_return"], -1)
        self.assertAlmostEqual(calc.returns(100, 0, 10, 1)["holding_period_return"], -0.9)

    def test_dcf_against_level_perpetuity(self):
        # Level FCFF 100 discounted at 10% is a perpetuity worth 1000.
        data = {"fcff_crore": [100] * 5, "discount_rate": 0.1, "terminal_growth": 0,
                "debt_crore": 200, "cash_crore": 50, "other_claims_crore": 50, "diluted_shares_crore": 10}
        result = calc.dcf(data, "nonfinancial")
        self.assertAlmostEqual(result["enterprise_value_crore"], 1000)
        self.assertAlmostEqual(result["present_value_per_share_inr"], 80)
        lower_rate = dict(data, discount_rate=0.09)
        self.assertGreater(calc.dcf(lower_rate, "nonfinancial")["enterprise_value_crore"], 1000)
        for changes in ({"terminal_growth": 0.1}, {"terminal_growth": -1}, {"fcff_crore": [100, -1]}):
            with self.assertRaises(ValueError):
                calc.dcf(dict(data, **changes), "nonfinancial")
        with self.assertRaises(ValueError):
            calc.dcf(data, "bank")


class CommandLine(unittest.TestCase):
    def test_saved_output_reproducibility_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "result.json"
            cmd = [sys.executable, str(ROOT / "scripts" / "calculate.py"),
                   str(ROOT / "tests" / "fixtures" / "bank.json"), "--output", str(target)]
            first = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            saved = target.read_bytes()
            self.assertEqual(json.loads(saved), calc.calculate(fixture("bank")))
            second = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(second.returncode, 2)
            self.assertEqual(target.read_bytes(), saved)

    def test_invalid_json_never_creates_result(self):
        with tempfile.TemporaryDirectory() as folder:
            source, target = Path(folder) / "bad.json", Path(folder) / "result.json"
            source.write_text('{"analysis_date":')
            result = subprocess.run([sys.executable, str(ROOT / "scripts" / "calculate.py"),
                                     str(source), "--output", str(target)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
