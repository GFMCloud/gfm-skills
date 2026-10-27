<!-- DEMO MATERIAL. Fernhill Logistics, Tallis Data and every
person and number below are invented. A case study a rep sends to operations directors after a
first call. -->

# How Fernhill Logistics cut failed overnight runs from one night in four to one in thirty

**The problem.** Fernhill runs 14 warehouses on a nightly batch that reconciles stock, orders and
carrier bookings. In early 2025 one run in four failed or finished late, and on those mornings
pickers started two hours behind. "We were paying overtime to catch up on work the system should
have done while we slept," says Priya Nair, Fernhill's operations director.

**What we found.** In a two-week review Tallis Data traced 70% of the failures to three jobs that
competed for the same database at 02:00, and a further 20% to one carrier feed that timed out.

**What changed.** We rescheduled the three jobs, added a retry with a time limit to the carrier
feed, and set up an alert that pages the on-call engineer before pickers arrive, not after.

**The result.** From March to August 2025 failed or late runs fell from 26% of nights to 3%.
First-shift overtime hours fell by 41% against the same months a year earlier.

**Seeing the same thing?** In 9 of the 12 reviews we ran last year, the operations team had at
least one nightly job that everyone worked around. If yours does, a 30-minute call with one of our engineers is usually enough
to tell whether a two-week review would find something. Reply to this email to pick a time.
