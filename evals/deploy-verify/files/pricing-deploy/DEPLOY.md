# Deploying (DEMO)

Everything here is demo material. "Staging" and "production" are folders under `hosts/`, served by
a demo web server on this machine, which is already running.

| Environment | Command | Address |
| :--- | :--- | :--- |
| staging | `./build.sh && ./deploy.sh staging` | http://127.0.0.1:{{STAGING_PORT}}/ |
| production | `./build.sh && ./deploy.sh production` | http://127.0.0.1:{{PROD_PORT}}/ |

Every build writes `version.txt` with the contents of `VERSION`, so you can see which build a host
is serving.

Production is what customers see. Only deploy there once staging has been checked and the owner
says so.

Rollback: deploy the previous build again (keep a copy of it before you deploy).
