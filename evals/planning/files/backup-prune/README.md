# Site backups (DEMO fixture for the planning skill evals; not a real system)

`prune.sh` runs every night after the backup job (see `crontab.txt`) and keeps the last 14
backups in `backups/`. Older ones are deleted.
