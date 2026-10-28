#!/usr/bin/env python3
"""Write the checker's demo fixtures into a folder: the current template's library plus good stages,
and one planted change per rule, plus the demo workflow they are checked against.
    python3 evals/wizard/rebuild-checker-fixtures.py <output folder>
check-fixtures.sh calls this with a fresh temporary folder, so the fixtures always match the template.
Names: good.sh and ok-*.sh must PASS with no WARN, warn-*.sh must PASS with a WARN, bad-*.sh must FAIL.
"""
import os
import sys

MARK = "# ===== STAGES"
HERE = os.path.dirname(os.path.abspath(__file__))
if len(sys.argv) != 2:
    sys.exit("usage: rebuild-checker-fixtures.py <output folder>")
OUT = sys.argv[1]
TPL = open(os.path.join(HERE, "..", "..", "skills", "wizard", "assets", "wizard-template.sh")).read()
LIB = TPL[:TPL.index(MARK)]

GOOD = '''# ===== STAGES: write the stages below this line =====

# DEMO fixture for the wizard checker: invented services and names.
WIZARD_TITLE="Demo shop: CI secrets"
WIZARD_ABOUT="Gets two demo keys into the keychain and into GitHub Actions for demo-org/shop-demo."
TOTAL_STAGES=3

main() {
  stage "Payments: secret key"
  open_url "https://dashboard.payments.example/keys"
  step "Click Create key, name it shop-demo-ci, copy the secret key."
  keychain_store PAYMENTS_SECRET_KEY "the payments secret key"
  if confirm_irreversible "Delete the old shop-demo key on the payments dashboard" "Anything still using it stops working."; then
    step "Click Delete on the old key."
    pause
    did "deleted the old payments key"
  else
    left "delete the old payments key when nothing uses it"
  fi

  stage "CDN: zone id and token"
  open_url "https://cdn.example/account/tokens"
  ask CDN_ZONE_ID "Zone id (shown on the zone overview, not secret):"
  keychain_store CDN_API_TOKEN "the CDN API token"

  stage "GitHub Actions"
  say "Copies the stored values into demo-org/shop-demo. Asks before each one."
  gh_secret PAYMENTS_SECRET_KEY demo-org/shop-demo keychain:PAYMENTS_SECRET_KEY
  gh_secret CDN_API_TOKEN demo-org/shop-demo keychain:CDN_API_TOKEN
  gh_variable CDN_ZONE_ID demo-org/shop-demo "$CDN_ZONE_ID"
  if confirm "Remove the old .env line for the payments key?"; then
    config_remove .env PAYMENTS_SECRET_KEY
  fi
}

_wizard_run "$@"
'''

KC = '  keychain_store CDN_API_TOKEN "the CDN API token"'
GH = '  gh_secret CDN_API_TOKEN demo-org/shop-demo keychain:CDN_API_TOKEN'
VARIANTS = {
    "good.sh": [],
    # must fail
    "bad-env-write.sh": [(KC, '  ask TOK "Token (not secret):"; printf "CDN_API_TOKEN=%s\\n" "$TOK" >> .env')],
    "bad-argv.sh": [(GH, '  gh secret set CDN_API_TOKEN --repo demo-org/shop-demo --body "$CDN_API_TOKEN"')],
    "bad-ask-secret.sh": [(KC, '  ask CDN_API_TOKEN "Paste the CDN API token:"')],
    "bad-ask-key.sh": [(KC, '  ask CDN_KEY "Paste the CDN key:"\n  config_set .env CDN_KEY "$CDN_KEY"')],
    "bad-count.sh": [("TOTAL_STAGES=3", "TOTAL_STAGES=4")],
    "bad-library.sh": [],  # library edited below
    "bad-example.sh": [('WIZARD_TITLE="Demo shop: CI secrets"', 'WIZARD_TITLE="EXAMPLE: replace this title"')],
    "bad-ci-name.sh": [("gh_secret PAYMENTS_SECRET_KEY demo-org", "gh_secret PAYMENT_SECRET_KEY demo-org")],
    "bad-xtrace.sh": [("main() {", "main() {\n  set -x")],
    "bad-direct-read.sh": [(KC, "  read -rs CDN_API_TOKEN\n  keychain_store CDN_API_TOKEN \"$CDN_API_TOKEN\"")],
    "bad-ifs-read.sh": [(KC, "  IFS= read -rs CDN_API_TOKEN; keychain_store CDN_API_TOKEN \"$CDN_API_TOKEN\"")],
    "bad-builtin-read.sh": [(KC, "  { builtin read -rs CDN_API_TOKEN; }; keychain_store CDN_API_TOKEN \"$CDN_API_TOKEN\"")],
    "bad-sed-env.sh": [("    config_remove .env PAYMENTS_SECRET_KEY", "    sed -i '' '/^PAYMENTS_SECRET_KEY=/d' .env")],
    "bad-tee-env.sh": [(KC, '  ask TOK "Token (not secret):"; printf "T=%s\\n" "$TOK" | tee -a .env')],
    "bad-op-document.sh": [(KC, "  op document create ./key.pem --title CDN_KEY_FILE")],
    "bad-security-flag.sh": [(KC, '  ask TOK "Value (not secret):"; security -q add-generic-password -a me -s CDN_API_TOKEN -w "$TOK"')],
    "bad-bash4.sh": [("main() {", "main() {\n  declare -A seen\n  seen[x]=1\n  say \"${seen[x]}\"")],
    "bad-bare-gate.sh": [("  say \"Copies the stored", "  confirm_irreversible \"Replace all three GitHub secrets\" \"Old values are gone.\"\n  say \"Copies the stored")],
    "bad-bare-confirm.sh": [("  if confirm \"Remove the old .env line for the payments key?\"; then\n    config_remove .env PAYMENTS_SECRET_KEY\n  fi",
                             "  confirm \"Remove the old .env line for the payments key?\"\n  config_remove .env PAYMENTS_SECRET_KEY")],
    "bad-arity.sh": [(KC, "  keychain_store CDN_API_TOKEN")],
    "bad-stage-in-helper.sh": [("main() {", "_cdn() {\n  stage \"CDN again\"\n}\n\nmain() {")],
    "bad-variable-secret.sh": [(GH, '  ask K "Paste it here:"\n  gh_variable CDN_API_TOKEN demo-org/shop-demo "$K"')],
    "bad-env-quoted.sh": [(KC, '  ask TOK "Value (not secret):"; printf "%s\\n" "T=$TOK" >> "$HOME/.env"; printf "x" >> ".env.local"')],
    "bad-bash4-quoted.sh": [("  say \"Copies the stored", "  ask ENVNAME \"Environment (not secret):\"\n  say \"${ENVNAME,,}\"\n  say \"Copies the stored")],
    "bad-else-confirm.sh": [("  if confirm \"Remove the old .env line for the payments key?\"; then\n    config_remove .env PAYMENTS_SECRET_KEY\n  fi",
                             "  if false; then note \"x\"\n  else confirm \"Remove the old .env line for the payments key?\"; fi\n  config_remove .env PAYMENTS_SECRET_KEY")],
    "bad-op-flag.sh": [(KC, "  op --account demo item create --vault Private --title X -")],
    "bad-op-flags.sh": [(KC, "  op --account demo --vault Demo item create --title X -")],
    "bad-syntax.sh": [('_wizard_run "$@"', 'if true; then\n_wizard_run "$@"')],
    # must pass with no warning
    "ok-prose-read.sh": [("name it shop-demo-ci, copy", "name it shop-demo-ci, then read the name back and copy")],
    "ok-total-comment.sh": [("TOTAL_STAGES=3", "TOTAL_STAGES=3  # one per service")],
    "ok-trailing-comment.sh": [('_wizard_run "$@"\n', '_wizard_run "$@"\n# end of wizard\n')],
    "ok-example-word.sh": [('  ask CDN_ZONE_ID "Zone id', '  ask SITE "Site name (EXAMPLE_SITE is staging):" EXAMPLE_SITE\n  ask CDN_ZONE_ID "Zone id')],
    "ok-elif-gate.sh": [("  if confirm_irreversible \"Delete", "  if false; then\n    note \"never\"\n  elif confirm_irreversible \"Delete")],
    "ok-dropdown.sh": [("  say \"Copies the stored", "  step \"Pick the zone from the drop-down, then click Cancel on the pop-up.\"\n  step \"Replace the placeholder text with the repo name.\"\n  say \"Copies the stored")],
    "ok-publishable.sh": [(KC, '  ask PUB_KEY "Publishable key (public, not secret):"\n  config_set .env PAYMENTS_PUBLISHABLE_KEY "$PUB_KEY"\n' + KC)],
    "ok-negated.sh": [("  say \"Copies the stored", "  note \"Do not delete the existing SPF record; never revoke the old token here.\"\n  say \"Copies the stored")],
    "ok-keycloak.sh": [("  say \"Copies the stored", "  ask KEYCLOAK_URL \"Keycloak address:\"\n  config_set app.conf KEYCLOAK_URL \"$KEYCLOAK_URL\"\n  ask HOCKEY_TEAM \"Team name:\"\n  config_set app.conf HOCKEY_TEAM \"$HOCKEY_TEAM\"\n  say \"Copies the stored")],
    "ok-function-keyword.sh": [("main() {", "function main {")],
    "ok-total-quoted.sh": [("TOTAL_STAGES=3", 'TOTAL_STAGES="3"')],
    # must pass with a warning
    "warn-no-gate.sh": [("  say \"Copies the stored", "  step \"Delete the old key on the payments dashboard.\"\n  say \"Copies the stored")],
    "warn-note-irreversible.sh": [("  say \"Copies the stored", "  note \"Now revoke the old CDN token.\"\n  say \"Copies the stored")],
}

WORKFLOW = """# DEMO fixture workflow for the wizard checker.
name: deploy
on: push
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - run: ./deploy.sh
        env:
          PAYMENTS_SECRET_KEY: ${{ secrets.PAYMENTS_SECRET_KEY }}
          CDN_API_TOKEN: ${{ secrets.CDN_API_TOKEN }}
          CDN_ZONE_ID: ${{ vars.CDN_ZONE_ID }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
"""

os.makedirs(os.path.join(OUT, "workflows"), exist_ok=True)
with open(os.path.join(OUT, "workflows", "deploy.yml"), "w") as fh:
    fh.write(WORKFLOW)
for name, changes in VARIANTS.items():
    stages = GOOD
    for old, new in changes:
        assert old in stages, (name, old)
        stages = stages.replace(old, new, 1)
    lib = LIB.replace("say()  { printf", "say()  { set -x; printf", 1) if name == "bad-library.sh" else LIB
    with open(os.path.join(OUT, name), "w") as fh:
        fh.write(lib + stages)
print(f"wrote {len(VARIANTS)} fixtures to {OUT}")
