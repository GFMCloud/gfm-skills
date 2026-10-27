# games-catalog

A hobby project that keeps an open catalogue of tabletop games. Everything it handles is public:
game titles and publishers from shop listings anyone can see, and links to public news posts.

- `match_titles.py`: matches each shop listing to a catalogue entry by title similarity. Scores
  between 0.60 and 0.88 go to `review/title_review.csv`, where a volunteer marks each pair `same`
  or `different` (and, for `different`, the right catalogue id or `none`).
- `triage_news.py`: for each news link, asks Claude (with a web fetch tool) whether the article
  announces a new edition of a catalogued game.
- `weekly_digest.py`: asks Claude to write the weekly email digest of catalogue changes.

About 400 listings a week reach `match_titles.py`; roughly 60 land in review. `data/shop_listings.csv` holds a sample of 43 listings; `review/title_review.csv` holds the 27 of them that reached review, with the volunteers' decisions.
