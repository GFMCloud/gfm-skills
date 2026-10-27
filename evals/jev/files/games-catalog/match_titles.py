"""Match shop listings to catalogue entries by title similarity (demo project)."""
import csv
from difflib import SequenceMatcher

ACCEPT = 0.88   # at or above: same game
REJECT = 0.60   # below: different game; between goes to review/title_review.csv


def norm(s):
    return " ".join(s.lower().replace("&", "and").replace("-", " ").split())


def best_match(title, catalog):
    scored = [(SequenceMatcher(None, norm(title), norm(c["title"])).ratio(), c) for c in catalog]
    return max(scored, key=lambda x: x[0])


def main():
    catalog = list(csv.DictReader(open("data/catalog.csv")))
    out, review = [], []
    for row in csv.DictReader(open("data/shop_listings.csv")):
        score, cat = best_match(row["title"], catalog)
        if score >= ACCEPT:
            out.append((row["listing_id"], cat["catalog_id"]))
        elif score >= REJECT:
            review.append((row["listing_id"], row["title"], cat["catalog_id"], cat["title"], round(score, 2)))
    print(f"matched {len(out)}, to review {len(review)}")


if __name__ == "__main__":
    main()
