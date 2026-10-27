# ledger-sync (DEMO project for a skill eval)

Syncs a demo ledger between two stores.

## Install
    pip install ledger-sync

## Usage
    ledger-sync run --dry-run
    ledger-sync status

## Options
| Flag | Default | Meaning |
| --- | --- | --- |
| --batch | 1000 | rows per batch |
| --dry-run | off | read and report, write nothing |
