# Moving crumb-demo.test from OldHost to NewHost (demo)

Agreed 2026-10-20. The new site is already built and deployed on NewHost at its preview address
https://crumb-demo.newhost.example (checked, works).

1. NewHost dashboard (https://dash.newhost.example), Sites, crumb-demo, Domains: add crumb-demo.test.
   NewHost then shows two nameservers (ns1/ns2.newhost.example) to use.
2. Lower the TTL on the current records at OldHost DNS first (OldHost panel, DNS, crumb-demo.test,
   set TTL to 300) and wait an hour, so the switch spreads quickly.
3. DemoReg (https://dash.demoreg.example), Domains, crumb-demo.test, Nameservers: replace the OldHost
   nameservers with NewHost's two. While it spreads, some visitors see each site.
4. Check https://crumb-demo.test shows the new site (the footer says "served by NewHost") from a
   couple of networks, and that NewHost's SSL certificate has been issued (Domains page shows it).
5. Only then: OldHost panel, Sites, crumb-demo, Delete site. OldHost keeps no backups after deletion.
   Cancel the OldHost plan after that (Billing, Cancel plan); the plan's last month is not refunded.
