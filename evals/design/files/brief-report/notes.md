<!-- Demo material for the brief-report eval. Fictional company and data. -->
# Help-centre migration: status notes

Status: ready to switch over after two steps. The new help centre (static site, 214 articles)
passes every check below. A reviewer playing a first-time customer called it "ready after small
fixes"; the fixes are in.

## To do before switch-over
1. Point help.example.test at the new host (DNS change, owner: you). Expect up to an hour to settle.
2. Turn off the old helpdesk widget in the app settings, so customers stop landing on retired pages.

## What changed for customers
Old: search, open a category, scroll a 40-item list, open the article, then a "was this helpful" form (5 actions).
New: search box on every page, answer opens inline (2 actions).

## Checks
| Check | Result | Detail |
| --- | --- | --- |
| Link checker | PASS | 214 articles, 1,902 links, 0 broken |
| Redirects | PASS | 186 old URLs redirect to the right new page |
| Phone, 390 px | PASS | no sideways scroll, search usable with one thumb |
| Search quality | PASS | 18 of 20 common questions answered in the top result |
| Accessibility | PASS | axe: 0 serious issues |
| Page weight | PASS | median 38 KB |
| First-time customer review | Ready after small fixes | 3 fixes, all in |
| Final review | Ready | no blocking issues |
| Dark mode | PASS | checked by hand |

## Rulings made during the build (12), with the cost if wrong
1. Kept article URLs where possible. Cost: none.
2. Dropped the "was this helpful" form. Cost: lose a weak signal.
3. Search runs in the browser, no server. Cost: index is 600 KB on first load.
4. Archived 31 articles older than 3 years. Cost: a rare question finds nothing.
5. Kept the old category names. Cost: none.
6. One template for every article. Cost: two long guides look plain.
7. No comments on articles. Cost: none.
8. Images converted to WebP. Cost: none.
9. Redirect map is a static file. Cost: must be edited by hand.
10. Search results capped at 10. Cost: rare long-tail misses.
11. Contact link on every page. Cost: maybe more tickets.
12. Launch on a Tuesday. Cost: none.

## Still untested
- Real customer traffic.
- The DNS change itself.
