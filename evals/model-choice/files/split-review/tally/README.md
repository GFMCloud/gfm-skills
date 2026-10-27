# tally

Demo material for a skill eval; not a real project.

A small command-line tool that prints word and line counts for text files, and the average words
per line, so writers can see how dense a draft is.

## Use

    python3 tally.py notes.txt chapter1.txt
    python3 tally.py --lines notes.txt      # line counts only

## Tests

    python3 -m unittest discover tests
