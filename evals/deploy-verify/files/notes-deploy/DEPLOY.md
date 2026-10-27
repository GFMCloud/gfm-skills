# Deploying (DEMO)

Everything here is demo material. Each environment is a folder under `hosts/`, served by a demo
web server on this machine.

| Environment | Command | Address |
| :--- | :--- | :--- |
| staging | `./build.sh && ./deploy.sh staging` | http://127.0.0.1:{{STAGING_PORT}}/ |
| production | `./build.sh && ./deploy.sh production` | http://127.0.0.1:{{PROD_PORT}}/ |

`version.txt` on each host shows which build it serves. Production is for customers: deploy there
only once staging is checked and the owner says so.
