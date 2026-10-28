# Sign-in move: loose notes (demo material)

We want to stop running our own password sign-in for the demo shop app (shop-app/) and use a
hosted sign-in service instead. Nobody has picked one yet.

Things people have raised, in no order:
- Do existing customers have to reset their passwords, or can their hashes move across?
- Staff accounts use the same login table as customers. Should they move too, or separately?
- The mobile app (another team) calls /login directly. What breaks for them?
- Someone mentioned "social login" but nobody knows if customers want it.
- What happens to customers who never log in again: do we move them at all?
- Cost: no idea how the services charge (per user? per sign-in?).
- Do we need to keep anything in the EU?

It's too big and too foggy to plan in one go. We'd like to work out the decisions over the next
few weeks, one at a time, before anyone builds anything.
