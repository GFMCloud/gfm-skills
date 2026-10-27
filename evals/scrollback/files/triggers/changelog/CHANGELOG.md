# Changelog (DEMO project for a skill eval)

## 1.4.0 (2026-10-20)
- Added: dry-run flag for `sync`.
- Fixed: importer no longer drops rows with an empty `issued_at`.

## 1.3.2 (2026-10-02)
- Fixed: exporter retries a rejected batch once, then stops.

## 1.3.0 (2026-09-15)
- Added: webhook signing.
- Changed: default batch size 500 to 1,000.
