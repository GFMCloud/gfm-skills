"""Sales tax. Prices in the catalogue already include tax; this splits it out for receipts."""
RATE = 0.20


def tax_included(gross):
    return round(gross - gross / (1 + RATE), 2)
