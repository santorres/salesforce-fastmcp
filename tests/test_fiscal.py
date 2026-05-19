"""Unit tests for fiscal-year and period-range helpers in channel_intelligence."""

import pytest
from datetime import date

import channel_intelligence as ci


class TestFiscalYearBoundaries:
    def test_fy_start_feb(self):
        # A date in May 2026 → FY starts Feb 1 2026
        assert ci._start_of_fiscal_year(date(2026, 5, 19)) == date(2026, 2, 1)

    def test_fy_start_rolls_back_for_jan(self):
        # January 2027 is still in FY27 (which started Feb 2026)
        assert ci._start_of_fiscal_year(date(2027, 1, 15)) == date(2026, 2, 1)

    def test_fy_end_derived_from_config(self):
        # FY that starts Feb 2026 must end Jan 31 2027
        end = ci._end_of_fiscal_year(date(2026, 5, 19))
        assert end == date(2027, 1, 31)

    def test_fy28_starts_feb_2027(self):
        r = ci._get_period_range("THIS_FISCAL_YEAR", now=date(2027, 3, 1))
        assert r["start"] == date(2027, 2, 1)
        assert r["end"] == date(2028, 1, 31)
        assert r["fiscal_label"] == "FY28"

    def test_fy_label_fy27(self):
        assert ci._fiscal_year_label(date(2026, 5, 19)) == "FY27"

    def test_fy_label_fy28(self):
        assert ci._fiscal_year_label(date(2027, 3, 1)) == "FY28"


class TestQuarterRanges:
    FY27 = date(2026, 5, 19)  # mid-FY27

    def test_q1_range(self):
        r = ci._get_period_range("Q1", now=self.FY27)
        assert r["start"] == date(2026, 2, 1)
        assert r["end"] == date(2026, 4, 30)
        assert r["fiscal_label"] == "FY27_Q1"

    def test_q2_range(self):
        r = ci._get_period_range("Q2", now=self.FY27)
        assert r["start"] == date(2026, 5, 1)
        assert r["end"] == date(2026, 7, 31)
        assert r["fiscal_label"] == "FY27_Q2"

    def test_q3_range(self):
        r = ci._get_period_range("Q3", now=self.FY27)
        assert r["start"] == date(2026, 8, 1)
        assert r["end"] == date(2026, 10, 31)
        assert r["fiscal_label"] == "FY27_Q3"

    def test_q4_crosses_year_boundary(self):
        r = ci._get_period_range("Q4", now=self.FY27)
        assert r["start"] == date(2026, 11, 1)
        assert r["end"] == date(2027, 1, 31)
        assert r["fiscal_label"] == "FY27_Q4"

    def test_current_quarter_in_q2(self):
        # May 2026 is Q2
        r = ci._get_period_range("CURRENT", now=self.FY27)
        assert r["quarter"] == "Q2"
        assert r["start"] == date(2026, 5, 1)

    def test_current_quarter_in_q4(self):
        r = ci._get_period_range("CURRENT", now=date(2026, 12, 1))
        assert r["quarter"] == "Q4"
        assert r["start"] == date(2026, 11, 1)

    def test_this_quarter_same_as_current(self):
        now = self.FY27
        assert ci._get_period_range("THIS_QUARTER", now=now)["start"] == \
               ci._get_period_range("CURRENT", now=now)["start"]

    def test_next_quarter(self):
        # In Q2 (May–Jul), next quarter = Q3
        r = ci._get_period_range("NEXT_QUARTER", now=self.FY27)
        assert r["quarter"] == "Q3"
        assert r["start"] == date(2026, 8, 1)

    def test_last_quarter(self):
        # In Q2, last quarter = Q1
        r = ci._get_period_range("LAST_QUARTER", now=self.FY27)
        assert r["quarter"] == "Q1"
        assert r["start"] == date(2026, 2, 1)

    def test_current_and_next_quarter(self):
        # Q2 + Q3
        r = ci._get_period_range("CURRENT_AND_NEXT_QUARTER", now=self.FY27)
        assert r["start"] == date(2026, 5, 1)
        assert r["end"] == date(2026, 10, 31)

    def test_current_and_next_spans_year(self):
        # Q4 + Q1: Nov 2026 → Apr 2027
        r = ci._get_period_range("CURRENT_AND_NEXT_QUARTER", now=date(2026, 11, 15))
        assert r["start"] == date(2026, 11, 1)
        assert r["end"] == date(2027, 4, 30)


class TestHistoricalPeriods:
    def test_historical_fy26_q1(self):
        r = ci._get_period_range("FY26_Q1")
        # FY26_Q1 in the codebase convention = Feb–Apr of calendar year 2026
        assert r["start"] == date(2026, 2, 1)
        assert r["end"] == date(2026, 4, 30)
        assert r["fiscal_label"] == "FY26_Q1"

    def test_historical_fy25_q4(self):
        r = ci._get_period_range("FY25_Q4")
        assert r["start"] == date(2025, 11, 1)
        assert r["end"] == date(2026, 1, 31)

    def test_last_fiscal_year(self):
        r = ci._get_period_range("LAST_FISCAL_YEAR", now=date(2026, 5, 19))
        assert r["start"] == date(2025, 2, 1)
        assert r["end"] == date(2026, 1, 31)
        assert r["fiscal_label"] == "FY26"

    def test_this_fiscal_year(self):
        r = ci._get_period_range("THIS_FISCAL_YEAR", now=date(2026, 5, 19))
        assert r["start"] == date(2026, 2, 1)
        assert r["end"] == date(2027, 1, 31)


class TestRollingPeriods:
    def test_last_30_days(self):
        now = date(2026, 5, 19)
        r = ci._get_period_range("LAST_30_DAYS", now=now)
        assert r["start"] == date(2026, 4, 20)
        assert r["end"] == now

    def test_next_60_days(self):
        now = date(2026, 5, 19)
        r = ci._get_period_range("NEXT_60_DAYS", now=now)
        assert r["start"] == now
        assert r["end"] == date(2026, 7, 18)


class TestNormalizePeriod:
    def test_typo_q1(self):
        assert ci._normalize_period("Q1?") == "Q1"

    def test_typo_with_dot(self):
        assert ci._normalize_period("Q2.") == "Q2"

    def test_alias_thisq(self):
        assert ci._normalize_period("THISQ") == "THIS_QUARTER"

    def test_alias_nextq(self):
        assert ci._normalize_period("NEXTQ") == "NEXT_QUARTER"

    def test_alias_lastq(self):
        assert ci._normalize_period("LASTQ") == "LAST_QUARTER"

    def test_alias_thisfy(self):
        assert ci._normalize_period("THISFY") == "THIS_FISCAL_YEAR"

    def test_fy_format_no_underscore(self):
        assert ci._normalize_period("FY26Q1") == "FY26_Q1"

    def test_fy_format_q_first(self):
        assert ci._normalize_period("Q1_FY26") == "FY26_Q1"

    def test_fy_format_quarter_word(self):
        assert ci._normalize_period("FY26_QUARTER1") == "FY26_Q1"

    def test_quarter_word(self):
        assert ci._normalize_period("QUARTER2") == "Q2"

    def test_spaces_converted(self):
        assert ci._normalize_period("THIS QUARTER") == "THIS_QUARTER"

    def test_lowercased_input(self):
        assert ci._normalize_period("q3") == "Q3"

    def test_unknown_passes_through(self):
        assert ci._normalize_period("SOME_THING") == "SOME_THING"


class TestInvalidPeriod:
    def test_unsupported_period_raises(self):
        with pytest.raises(ValueError, match="Unsupported period"):
            ci._get_period_range("NOT_A_PERIOD")
