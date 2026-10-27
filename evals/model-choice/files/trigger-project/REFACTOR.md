# Refactor: split kiln.py (Demo material for a skill eval; not a real project.)

kiln.py is 900 lines in the real project (shortened here). Split it into log.py, curves.py and
cli.py with no behaviour change. Tests cover the CLI end to end.
