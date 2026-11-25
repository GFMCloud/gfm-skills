<!-- Demo material for the brief-comparison eval. Fictional tools and data. -->
# Backup tools for the team laptops: research notes

Recommendation: Driftsafe by default; Copperline if you need to restore whole machines; skip
Tallybox (no release in 8 months); Northvault only if you already pay for its cloud.

## Pick by need
- Files from laptops, to our own NAS: Driftsafe.
- Whole-machine restore after a disk dies: Copperline.
- Already pay for Northvault cloud storage: Northvault.
- Need a free licence for 10+ laptops: Driftsafe (free under 25 seats).

## Feature grid
| | Driftsafe | Copperline | Tallybox | Northvault |
| --- | --- | --- | --- | --- |
| Runs locally | yes | yes | yes | client only |
| Target: NAS | yes | yes | yes | no |
| Target: cloud | S3-compatible | no | S3-compatible | own cloud only |
| Whole-machine image | no | yes | no | no |
| Encryption at rest | yes | yes | yes | yes |
| Client-side keys | yes | yes | no | optional |
| Deduplication | yes | yes | partial | yes |
| Versioning | 90 days | 30 days | 14 days | 1 year |
| macOS | yes | yes | yes | yes |
| Windows | yes | yes | no | yes |
| Admin console | web | desktop | none | web |
| Price | free under 25 seats | 40 per machine once | free | 6 per user per month |
| Licence | Apache-2.0 | proprietary | MIT | proprietary |
| Last release | 2 weeks ago | 1 month ago | 8 months ago | 1 week ago |
| Stars / users | 6,100 stars | 2,000 customers | 900 stars | not published |

## Safety notes
- Tallybox stores keys server-side by default.
- Northvault sends file names to its cloud even when contents are encrypted.
- Copperline's image restore needs a USB stick per machine.
