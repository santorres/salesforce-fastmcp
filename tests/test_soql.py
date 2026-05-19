"""Unit tests for SOQL helper functions in channel_intelligence."""

import pytest
from datetime import date

import channel_intelligence as ci


class TestEscapeSoql:
    def test_plain_string_unchanged(self):
        assert ci._escape_soql("Accenture") == "Accenture"

    def test_apostrophe_escaped(self):
        assert ci._escape_soql("O'Brien") == "O\\'Brien"

    def test_backslash_escaped(self):
        assert ci._escape_soql("path\\name") == "path\\\\name"

    def test_both_escaped(self):
        result = ci._escape_soql("it's a\\test")
        assert result == "it\\'s a\\\\test"

    def test_empty_string(self):
        assert ci._escape_soql("") == ""


class TestClampLimit:
    def test_default_returned_when_none(self):
        assert ci._clamp_limit(None, default=10, max_val=50) == 10

    def test_value_returned_within_range(self):
        assert ci._clamp_limit(25, default=10, max_val=50) == 25

    def test_clamped_to_max(self):
        assert ci._clamp_limit(100, default=10, max_val=50) == 50

    def test_zero_raises(self):
        with pytest.raises(ValueError, match="positive"):
            ci._clamp_limit(0, default=10, max_val=50)

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            ci._clamp_limit(-5, default=10, max_val=50)

    def test_exactly_max_allowed(self):
        assert ci._clamp_limit(50, default=10, max_val=50) == 50

    def test_string_int_coerced(self):
        assert ci._clamp_limit("20", default=10, max_val=50) == 20


class TestBuildOppWhere:
    RANGE = {
        "start": date(2026, 2, 1),
        "end": date(2026, 4, 30),
    }

    def test_open_mode_adds_isclosed_false(self):
        where = ci._build_opp_where(closed_mode="open", range_=self.RANGE, channel_manager="")
        assert "IsClosed = false" in where

    def test_won_mode_adds_stagename(self):
        where = ci._build_opp_where(closed_mode="won", range_=self.RANGE, channel_manager="")
        assert "StageName = 'Closed Won'" in where

    def test_won_mode_no_isclosed(self):
        where = ci._build_opp_where(closed_mode="won", range_=self.RANGE, channel_manager="")
        assert "IsClosed" not in where

    def test_closed_mode_adds_isclosed_true(self):
        where = ci._build_opp_where(closed_mode="closed", range_=self.RANGE, channel_manager="")
        assert "IsClosed = true" in where

    def test_no_mode_no_stage_filter(self):
        where = ci._build_opp_where(closed_mode=None, range_=self.RANGE, channel_manager="")
        assert "IsClosed" not in where
        assert "StageName" not in where

    def test_channel_manager_included(self):
        where = ci._build_opp_where(closed_mode=None, range_=self.RANGE, channel_manager="Jane")
        assert "Channel_Manager__c = 'Jane'" in where

    def test_channel_manager_omitted_when_empty(self):
        where = ci._build_opp_where(closed_mode=None, range_=self.RANGE, channel_manager="")
        assert "Channel_Manager__c" not in where

    def test_channel_manager_escaped(self):
        where = ci._build_opp_where(closed_mode=None, range_=self.RANGE, channel_manager="O'Brien")
        assert "Channel_Manager__c = 'O\\'Brien'" in where

    def test_date_range_present(self):
        where = ci._build_opp_where(closed_mode=None, range_=self.RANGE, channel_manager="")
        assert "CloseDate >= 2026-02-01" in where
        assert "CloseDate <= 2026-04-30" in where

    def test_countries_filter_present(self):
        where = ci._build_opp_where(closed_mode=None, range_=self.RANGE, channel_manager="")
        assert "Account.BillingCountry IN" in where

    def test_extra_conditions_anded(self):
        where = ci._build_opp_where(
            closed_mode=None,
            range_=self.RANGE,
            channel_manager="",
            extra_conditions=["Partner__c = null", "Amount > 0"],
        )
        assert "Partner__c = null" in where
        assert "Amount > 0" in where

    def test_empty_extra_condition_skipped(self):
        where = ci._build_opp_where(
            closed_mode=None,
            range_=self.RANGE,
            channel_manager="",
            extra_conditions=["", "Amount > 0"],
        )
        parts = where.split(" AND ")
        # Empty string should not appear as a clause
        assert "" not in parts
