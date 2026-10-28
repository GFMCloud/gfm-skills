# tile-api

<!-- Demo material for a skill trial, not real. -->

This is the API for the tile shop. It is written in TypeScript and runs on Node.

## About the project

The tile shop started as a small family business selling bathroom tiles and grew into an online
shop with a warehouse. The API serves the web shop and the warehouse app. Old invoices are
re-printed through `src/pricing-legacy/`, which is the only reason that folder still exists.

## Layout

- `src/routes/` holds the HTTP routes
- `src/db/` holds the database code and migrations
- `src/pricing/` holds the price calculation
- `test/` holds the tests

## Commands

- `npm run dev` starts the dev server
- `npm test` runs the tests
- `npm run lint` runs the linter
- `npm run db:migrate` runs the migrations
- `npm run db:seed` loads the demo data

## Rules

1. Read the code you are changing before you change it.
2. Run `npm run db:migrate` before `npm run db:seed`: the seed data needs the columns the latest
   migration adds, and seeding first fails halfway and leaves half a catalogue.
3. Write clean, readable code.
4. Don't use the old pricing module in `src/pricing-legacy/`.
5. Prices are whole pence in an integer column; never store a price as a float.
6. Handle errors properly.
7. Run `npm test` before saying a change is done; CI runs the same tests and blocks the merge.
8. Indent with two spaces.
9. A new route gets a test in `test/routes/` with the same file name as the route.
