"""Reads config.ini."""
import configparser
from collections import namedtuple
from datetime import date

Config = namedtuple("Config", "statuses since columns")


def _list(value):
    return [v.strip() for v in value.split(",") if v.strip()]


def read(path):
    cp = configparser.ConfigParser()
    if not cp.read(path):
        raise FileNotFoundError(path)
    s = cp["export"]
    return Config(
        statuses=set(_list(s.get("statuses", "paid"))),
        since=date.fromisoformat(s.get("since", "2000-01-01")),
        columns=_list(s["columns"]),
    )
