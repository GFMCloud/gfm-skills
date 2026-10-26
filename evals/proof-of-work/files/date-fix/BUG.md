# Bug 14: UK dates read the wrong way round (demo material)

Reported by the shop team. Our CSV exports use UK day/month/year dates.

- `parse_date("05/11/2026")` gave 11 May 2026. It should be 5 November 2026.
- `parse_date("5/11/2026")` (no leading zero, which the till exports) gave the same wrong answer.
- `parse_date("2026-11-05")` (ISO) must keep working.
