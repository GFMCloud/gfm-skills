"""Price lookup from the catalogue file."""
import json
import os
from functools import lru_cache

_CATALOG = os.path.join(os.path.dirname(__file__), "catalog.json")


@lru_cache(maxsize=None)
def catalog():
    with open(_CATALOG) as f:
        return json.load(f)


def price_of(sku):
    try:
        return catalog()[sku]["price"]
    except KeyError:
        raise KeyError(f"unknown sku {sku}") from None
