# Grill so far: newsletter signup (DEMO FIXTURE, not a real conversation)

Subject: add a newsletter signup to the bakery website.

## Round 1 (asked by the agent)

Round 1. Settled 0, open 4, waiting on lookups 0.
Found: site mails through the shop's own SMTP account (site/mail.config.json).

**Q1. Confirmation step.** Should new signups confirm by clicking a link in an email before they
are added (double opt-in)?
Recommended: yes. It keeps typos and fake addresses off the list and is the safer reading of
consent rules.

**Q2. Sending service.** Use a newsletter service (list hosting, unsubscribe links and bounce
handling built in) rather than sending from the shop's own SMTP account?
Recommended: yes. Unsubscribe and bounce handling are fiddly to build and get wrong.

**Q3. Where the form goes.** Put the signup form in the footer of every page?
Recommended: yes. One form, seen everywhere, no new page to maintain.

**Q4. What to collect.** Collect the email address only?
Recommended: yes. Every extra field lowers signups.

## The user's answers

1 yes. 2 no, I'm not paying for another service, we send from our own SMTP. 3 your call.
4 no, also first name so the email can say "Hi Sam".
