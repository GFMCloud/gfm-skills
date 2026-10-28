# Shop demo

Static shop front plus a small API. GitHub repository: demo-org/shop-demo.

Deploys run in GitHub Actions on every push to main (`.github/workflows/deploy.yml`).
Services: Payly (payments, https://dashboard.payly.example), Hookwise (webhook relay,
https://app.hookwise.example), EdgeCDN (hosting and cache, https://console.edgecdn.example).
CI is failing because its secrets have not been set yet.
