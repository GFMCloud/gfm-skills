# payhook (DEMO)

Demo project for a debugging eval. The payment provider, URLs, events and keys are invented.

Receives payment webhooks from the provider and records them in the ledger. In production it runs
behind the web server at the URL in `config.ini`; `payhook.app.handle()` is the whole request path.

The signing secret comes from the `PAYHOOK_SECRET` environment variable.
Tests: `python3 -m unittest discover -s tests -t .`
