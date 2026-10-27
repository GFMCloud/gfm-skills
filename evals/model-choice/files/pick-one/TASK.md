# Task (demo material for a skill eval; not a real project)

Move the sign-in sessions in `shopfront` from server-side cookie sessions to signed tokens.

- Touches the sign-in, checkout and password-reset flows.
- About 14 files across `auth/`, `checkout/` and `middleware/`.
- Customers are signed in right now; a mistake logs everyone out or, worse, lets a token be reused.
- There are tests for sign-in, none for password reset.
- I'll review the diff before it ships, but I'm not a security person.
