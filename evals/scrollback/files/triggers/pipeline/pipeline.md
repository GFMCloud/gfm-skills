# Sync pipeline (DEMO for a skill eval)
1. A nightly timer starts the importer.
2. The importer reads the source store in batches of 1,000 and writes to a staging table.
3. Dedupe merges rows with the same ledger id.
4. The exporter writes clean rows to the target store and posts a webhook per batch.
