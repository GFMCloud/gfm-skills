# Incident 2026-10-22 (Demo material for a skill trial, not real.)

- 14:02 deploy of v2.3 to the demo shop; checkout page blank.
- 14:10 rolled back. Cause: the build used a stale `.env.production` with the old API host.
- 14:30 fixed the env file, redeployed, checkout OK.
- Same thing happened in August.
