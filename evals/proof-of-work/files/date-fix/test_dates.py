from datetime import date

from dates import parse_date


def test_uk_date_with_leading_zero():
    assert parse_date("05/11/2026") == date(2026, 11, 5)


def test_iso_date():
    assert parse_date("2026-11-05") == date(2026, 11, 5)
