# release-notes

Builds the release notes for `tidyplot`, an open-source plotting library (demo project). The
repository and its pull requests are public. `classify_prs.py` makes two Claude calls:

1. for each merged pull request, decide whether it is user-facing (`yes` or `no`), from its title,
   description and list of changed files;
2. write the release-notes prose from the user-facing ones.

About 120 pull requests per release. Maintainers corrected the user-facing labels for the last two
releases; those are in `data/past_labels.csv`.
