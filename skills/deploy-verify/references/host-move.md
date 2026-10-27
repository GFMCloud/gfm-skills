# Moving a site to a new host or domain

The aim: visitors never notice. The old host stays up and unchanged until the new one is proven
and the DNS change has settled; then the old one is retired, on the owner's say.

## 1. Inventory the old site

Before building anything on the new host, write down what the old one does: every page and file
(crawl it: `check_site.py <old-url> --pages 500`), redirects, the custom 404 page, headers that
matter, forms and where they post, anything built at deploy time (a build command, environment
variables), and how deploys happen now (a push to a branch, a scheduled job, a manual upload).

## 2. Stand the new host up beside it

Deploy to the new host's own address (its preview or `*.example-host.app` style name) while the
domain still points at the old one. Some hosts need a browser step to connect a git provider or
to add a custom domain; plan it as a step for the user rather than trying to script around it.

If the new host builds from git on every push, **the push is the deploy**: verify at the URL, not
in the host's dashboard.

## 3. Prove parity before touching DNS

Crawl the **old** host and compare each thing it finds with the new one, so every old page is looked
for; then check the new host on its own for anything broken there:

```
python3 <skill>/scripts/check_site.py <old-url> --compare <new-url> --pages 500
python3 <skill>/scripts/check_site.py <new-url> --pages 500
```

Comparing the other way round only finds old pages that something on the new host still links to.
Every page and file must answer the same way on both: same status, same final path, same bytes.
Go through each difference; don't wave one off:

- **"Pretty URL" redirects.** Many static hosts answer `/about.html` with a 308 to `/about`. Some
  tools (Python before 3.11, for one) don't follow 308, so a checker can report this as a failure
  when the page is fine. `check_site.py` follows it and shows the chain; decide whether the
  changed address matters (old links still land, search results still resolve) and say so.
- A page missing on the new host is a blocker until it's copied or deliberately dropped.
- Different bytes on a page that should be static: find out why (build time stamps are harmless;
  a stale copy is not).

## 4. Change DNS: one record, with a way back

**Read the whole zone first** (an export, or `dig` for MX, TXT, A, AAAA and CNAME records).
Mail (MX), mail security (SPF, DKIM, DMARC TXT records) and other subdomains often live in the
same zone.

- **Change only the record for this site.** Some hosts' setup wizards offer to "manage your DNS",
  which means moving the whole zone's nameservers to them. That moves mail and every other record
  too, and anything not copied over exactly stops working. Unless the owner has decided to move
  the zone, decline it and add the one record (usually a CNAME) at the current DNS provider. If
  the wizard only shows a nameserver change, you are on the wrong path; look for the "add records
  yourself" option.
- **Write down the old record's exact value** before changing it. Restoring it is the rollback.
- **Lower the record's TTL** (to 300 seconds, say) a full old-TTL period before the switch, so a
  rollback takes minutes, not a day.
- **A DNS change is the owner's step or needs their yes**, naming the record and the new value.
  It is never part of "check that it works". If the planning skill is installed, write this step
  as a plan with it and stop for the yes.

After the change, check from outside your own cache: `dig +short <name> @<the zone's
nameserver>`, then a public resolver, then `check_site.py <https://the-domain>` to confirm the new
host answers with a valid certificate. Certificates can take a few minutes to issue after the
record changes; poll with a limit.

## 5. Retire the old host, later

Keep the old host up, unchanged, until the old TTL has passed several times over and the new host
has served real traffic cleanly (a few days is common). Switching it off or deleting it needs the
owner's yes. Note anything that still pointed at the old host (a scheduled build, a webhook) and
move or stop it.

## Report

What moved, the parity result (pages compared, differences and what each was), the DNS change
made or proposed (record, old value, new value, TTL), how to roll back, the `Live check:` line for
the domain and the `Not checked:` list.
