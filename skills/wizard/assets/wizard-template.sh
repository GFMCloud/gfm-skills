#!/usr/bin/env bash
# A wizard: walks you through steps only you can do, one stage at a time.
# Run it yourself in a terminal: bash <this file>. Stop with Ctrl-C at any point;
# running it again offers back what was already stored.
# Secrets are typed hidden and go straight into the macOS keychain or 1Password.
# They are never written to a file, put on a command line or printed.
#
# Everything above the STAGES line is the wizard library. Leave it as it is.
set -euo pipefail
set +x

TOTAL_STAGES=0
WIZARD_TITLE="Wizard"
WIZARD_ABOUT=""
_stage_no=0
_did=()
_left=()
_acct="${USER:-$(id -un)}"
_here=$(cd "$(dirname "$0")" && pwd)
_tty=$(stty -g 2>/dev/null || true)

if [ -t 1 ]; then
  _b=$'\033[1m'; _d=$'\033[2m'; _g=$'\033[32m'; _y=$'\033[33m'; _r=$'\033[0m'
else
  _b=""; _d=""; _g=""; _y=""; _r=""
fi

say()  { printf '  %s\n' "$*"; }
step() { printf '  %s>%s %s\n' "$_b" "$_r" "$*"; }
note() { printf '  %s%s%s\n' "$_d" "$*" "$_r"; }
warn() { printf '  %s! %s%s\n' "$_y" "$*" "$_r"; }

# did "text": record something finished. left "text": record something still to do by hand.
did()  { _did+=("$*"); printf '  %sdone:%s %s\n' "$_g" "$_r" "$*"; }
left() { _left+=("$*"); warn "left for you: $*"; }

# _line VAR: read one line from the terminal into VAR. End of input stops the wizard.
_line() {
  local _got
  if ! IFS= read -r _got; then
    printf '\n'; warn "No more input, so the wizard stops here."; exit 3
  fi
  printf -v "$1" '%s' "$_got"
}

# _drain: throw away lines still waiting (a multi-line paste). Succeeds only if there were some.
_drain() {
  local _junk _n=0
  while IFS= read -rs -t 1 _junk; do _n=1; done
  _junk=""
  [ "$_n" -eq 1 ]
}

_need() { # _need HELPER COUNT ARGS...: true when the first COUNT args are all non-empty
  local _h=$1 _c=$2 _i=1
  shift 2
  while [ "$_i" -le "$_c" ]; do
    if [ -z "${!_i:-}" ]; then left "$_h is missing argument $_i, so that step was skipped"; return 1; fi
    _i=$((_i + 1))
  done
}

# stage "Title": start the next stage and show how many are left.
stage() {
  _stage_no=$((_stage_no + 1))
  printf '\n%s== Stage %d of %d: %s ==%s\n' "$_b" "$_stage_no" "$TOTAL_STAGES" "${1:-}" "$_r"
  note "$((TOTAL_STAGES - _stage_no)) left after this one"
}

# open_url URL: open a page in the browser and always print it too.
open_url() {
  printf '  open: %s\n' "${1:-}"
  if [ "$(uname -s)" = Darwin ] && command -v open >/dev/null 2>&1; then
    open "$1" >/dev/null 2>&1 || note "Could not open the browser. Open the link above yourself."
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$1" >/dev/null 2>&1 || note "Could not open the browser. Open the link above yourself."
  else
    note "Open the link above in your browser."
  fi
}

# pause ["message"]: wait until the user has done the step on screen.
pause() {
  local _x
  printf '  %s%s%s ' "$_d" "${1:-Press Enter when that is done.}" "$_r"
  _line _x
}

# ask VAR "Prompt" [default]: a visible answer. Never use it for a secret.
ask() {
  _need ask 2 "$@" || return 0
  local _var=$1 _prompt=$2 _def=${3:-} _ans
  if [ -n "$_def" ]; then
    printf '  %s%s%s [%s] ' "$_b" "$_prompt" "$_r" "$_def"
  else
    printf '  %s%s%s ' "$_b" "$_prompt" "$_r"
  fi
  _line _ans
  if [ -z "$_ans" ]; then _ans=$_def; fi
  printf -v "$_var" '%s' "$_ans"
}

# confirm "Question": yes or no, no is the default. Always use it inside if (or with &&).
confirm() {
  local _a
  printf '  %s? %s [y/N]%s ' "$_y" "${1:-Go ahead?}" "$_r"
  _line _a
  case $_a in y|Y|yes|Yes|YES) return 0 ;; *) return 1 ;; esac
}

# confirm_irreversible "What will happen" ["Why it can't be undone"]: true only on a typed yes.
# Always use it inside if (or with &&).
confirm_irreversible() {
  local _a
  printf '\n  %s%sCannot be undone:%s %s\n' "$_y" "$_b" "$_r" "${1:-}"
  if [ -n "${2:-}" ]; then note "$2"; fi
  printf '  Type yes to go ahead, anything else to skip: '
  _line _a
  [ "$_a" = yes ]
}

_check_name() {
  case $1 in
    ''|-*|*[!A-Za-z0-9_.-]*) warn "Bad item name '$1' (letters, digits, _ . - only, not starting with -)."; return 1 ;;
  esac
}

# keychain_store ITEM "what it is": hidden entry straight into the macOS keychain.
# The keychain's own prompt takes the value, so it never sits in this script. One line only.
keychain_store() {
  _need keychain_store 2 "$@" || return 0
  local _item=$1 _what=$2
  _check_name "$_item" || { left "store $_what (bad item name)"; return 0; }
  if ! command -v security >/dev/null 2>&1; then
    left "store $_what as $_item: no macOS keychain on this machine"; return 0
  fi
  if security find-generic-password -a "$_acct" -s "$_item" >/dev/null 2>&1; then
    if ! confirm "$_item is already in the keychain. Replace it?"; then
      did "kept the keychain item $_item"; return 0
    fi
  fi
  say "Paste $_what at the prompt below. Typing is hidden, and it asks twice."
  if security add-generic-password -U -a "$_acct" -s "$_item" -l "$_item" -w; then
    if _drain; then
      left "$_what was more than one line, so the keychain item $_item holds only part of it. Replace it; a multi-line key belongs in a file kept in your password manager"
    else
      did "stored $_what in the keychain as $_item"
    fi
  else
    _drain || true
    left "store $_what in the keychain as $_item (the keychain did not take it)"
  fi
}

# op_store ITEM "what it is" VAULT: hidden entry straight into 1Password. One line only.
# The value goes to the op command on standard input, never as an argument.
op_store() {
  _need op_store 3 "$@" || return 0
  local _item=$1 _what=$2 _vault=$3 _v="" _v2=""
  _check_name "$_item" || { left "store $_what (bad item name)"; return 0; }
  if ! command -v op >/dev/null 2>&1; then
    left "store $_what in 1Password as $_vault/$_item: the op command is not installed"; return 0
  fi
  if ! op vault get "$_vault" >/dev/null 2>&1; then
    left "store $_what in 1Password as $_vault/$_item: not signed in, or no vault named $_vault"; return 0
  fi
  if op item get "$_item" --vault "$_vault" >/dev/null 2>&1; then
    if ! confirm "$_item is already in 1Password ($_vault). Move the old one to the 1Password archive and store a new one?"; then
      did "kept the 1Password item $_vault/$_item"; return 0
    fi
    if ! op item delete "$_item" --vault "$_vault" --archive >/dev/null 2>&1; then
      left "replace $_vault/$_item in 1Password (could not archive the old item)"; return 0
    fi
    note "Old item moved to the 1Password archive; restore it from there if needed."
  fi
  printf '  %sPaste %s (typing is hidden):%s ' "$_b" "$_what" "$_r"
  if ! IFS= read -rs _v; then printf '\n'; warn "No more input, so the wizard stops here."; exit 3; fi
  printf '\n'
  if _drain; then
    _v=""; left "store $_what in 1Password as $_vault/$_item: it was more than one line; keep a multi-line key as a file in 1Password instead"; return 0
  fi
  printf '  Paste it again to check: '
  if ! IFS= read -rs _v2; then printf '\n'; warn "No more input, so the wizard stops here."; exit 3; fi
  printf '\n'
  _drain || true
  if [ -z "$_v" ] || [ "$_v" != "$_v2" ]; then
    _v=""; _v2=""; left "store $_what in 1Password as $_vault/$_item (empty, or the two entries differed)"; return 0
  fi
  _v2=""
  case $_v in *[[:cntrl:]]*)
    _v=""; left "store $_what in 1Password as $_vault/$_item (it held control characters)"; return 0 ;;
  esac
  _v=${_v//\\/\\\\}
  _v=${_v//\"/\\\"}
  if printf '{"title":"%s","category":"PASSWORD","fields":[{"id":"password","type":"CONCEALED","purpose":"PASSWORD","label":"password","value":"%s"}]}' "$_item" "$_v" \
      | op item create --vault "$_vault" - >/dev/null 2>&1; then
    did "stored $_what in 1Password as op://$_vault/$_item/password"
  else
    left "store $_what in 1Password as $_vault/$_item (op did not take it)"
  fi
  _v=""
}

# _fetch VAR SOURCE: read a stored secret into VAR. SOURCE is keychain:ITEM or op://vault/item/field.
_fetch() {
  local _src=$2 _got=""
  case $_src in
    keychain:*) _got=$(security find-generic-password -a "$_acct" -s "${_src#keychain:}" -w 2>/dev/null) || return 1 ;;
    op://*)     _got=$(op read --no-newline "$_src" 2>/dev/null) || return 1 ;;
    *) return 1 ;;
  esac
  [ -n "$_got" ] || return 1
  printf -v "$1" '%s' "$_got"
}

_gh_ready() {
  command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1
}

# gh_secret NAME OWNER/REPO SOURCE: copy a stored secret into a GitHub Actions secret.
# The value goes from the store to gh on standard input. Asks first; replacing needs a typed yes.
gh_secret() {
  _need gh_secret 3 "$@" || return 0
  local _name=$1 _repo=$2 _src=$3 _v="" _list=""
  if ! _gh_ready; then
    left "GitHub secret $_name in $_repo: gh is missing or not signed in (gh auth login, then run this again)"; return 0
  fi
  if ! _list=$(gh secret list --repo "$_repo" 2>/dev/null); then
    if ! confirm_irreversible "Set the GitHub secret $_name in $_repo. Could not list the repo's secrets, so this may replace an existing one" "GitHub never shows a secret's value, so a replaced one is gone."; then
      left "GitHub secret $_name in $_repo (could not check it, and you chose not to set it)"; return 0
    fi
  elif printf '%s\n' "$_list" | cut -f1 | grep -qx "$_name"; then
    if ! confirm_irreversible "Replace the GitHub secret $_name in $_repo" "GitHub never shows a secret's value, so the old one is gone once replaced."; then
      left "GitHub secret $_name in $_repo (you chose not to replace it)"; return 0
    fi
  elif ! confirm "Set the GitHub secret $_name in $_repo now?"; then
    left "GitHub secret $_name in $_repo (skipped)"; return 0
  fi
  if ! _fetch _v "$_src"; then
    left "GitHub secret $_name in $_repo: nothing stored at $_src yet"; return 0
  fi
  if printf '%s' "$_v" | gh secret set "$_name" --repo "$_repo" >/dev/null 2>&1; then
    did "set the GitHub secret $_name in $_repo (from $_src)"
  else
    left "GitHub secret $_name in $_repo: gh did not take it"
  fi
  _v=""
}

# gh_variable NAME OWNER/REPO VALUE: set a GitHub Actions variable. Not for secrets.
gh_variable() {
  _need gh_variable 3 "$@" || return 0
  local _name=$1 _repo=$2 _value=$3
  if ! _gh_ready; then
    left "GitHub variable $_name=$_value in $_repo: gh is missing or not signed in"; return 0
  fi
  if ! confirm "Set the GitHub variable $_name to $_value in $_repo?"; then
    left "GitHub variable $_name=$_value in $_repo (skipped)"; return 0
  fi
  if gh variable set "$_name" --repo "$_repo" --body "$_value" >/dev/null 2>&1; then
    did "set the GitHub variable $_name=$_value in $_repo"
  else
    left "GitHub variable $_name=$_value in $_repo: gh did not take it"
  fi
}

_config_path() { # _config_path VAR FILE: absolute path; a relative FILE is taken from the wizard's folder
  local _f=$2
  case $_f in /*) ;; *) _f="$_here/$_f" ;; esac
  printf -v "$1" '%s' "$_f"
}

# config_set FILE KEY VALUE: put KEY=VALUE in a config file, replacing an old KEY line.
# A relative FILE is taken from the wizard's own folder, wherever it is run from.
# For values that are not secret, or an op:// reference. Refuses secret-looking keys otherwise.
config_set() {
  _need config_set 2 "$@" || return 0
  local _file _key=$2 _value=${3:-} _tmp
  _config_path _file "$1"
  case $_key in *[!A-Za-z0-9_]*) left "set $_key in $_file (bad key name)"; return 0 ;; esac
  case $_value in
    op://*) ;;
    *) case $(printf '%s' "$_key" | tr '[:lower:]' '[:upper:]') in
         *PUBLISHABLE*|*PUBLIC*) ;;
         KEY|KEYS|*_KEY|*_KEYS|KEY_*|*_KEY_*|TOKEN|*_TOKEN|*_TOKENS|TOKEN_*|*_TOKEN_*|*SECRET*|*PASSWORD*|*PRIVATE*)
           left "set $_key in $_file: that looks like a secret, so it belongs in the keychain or 1Password"; return 0 ;;
       esac ;;
  esac
  if [ ! -d "$(dirname "$_file")" ]; then left "set $_key in $_file (its folder does not exist)"; return 0; fi
  _tmp=$(mktemp)
  if [ -f "$_file" ]; then grep -v "^${_key}=" "$_file" > "$_tmp" || true; fi
  printf '%s=%s\n' "$_key" "$_value" >> "$_tmp"
  cat "$_tmp" > "$_file"
  rm -f "$_tmp"
  did "set $_key in $_file"
}

# config_remove FILE KEY: delete KEY's line from a config file (an old plain-text secret, say).
config_remove() {
  _need config_remove 2 "$@" || return 0
  local _file _key=$2 _tmp
  _config_path _file "$1"
  case $_key in *[!A-Za-z0-9_]*) left "remove $_key from $_file (bad key name)"; return 0 ;; esac
  if [ ! -f "$_file" ] || ! grep -q "^${_key}=" "$_file"; then
    note "$_key is not in $_file; nothing to remove."; return 0
  fi
  _tmp=$(mktemp)
  grep -v "^${_key}=" "$_file" > "$_tmp" || true
  cat "$_tmp" > "$_file"
  rm -f "$_tmp"
  did "removed the $_key line from $_file"
}

_summary() {
  local _rc=${1:-0} _i
  if [ -n "$_tty" ]; then stty "$_tty" 2>/dev/null || true; fi
  printf '\n%s== %s: what happened ==%s\n' "$_b" "$WIZARD_TITLE" "$_r"
  if [ ${#_did[@]} -gt 0 ]; then
    for _i in "${_did[@]}"; do say "done: $_i"; done
  else
    say "Nothing was done."
  fi
  if [ ${#_left[@]} -gt 0 ]; then
    for _i in "${_left[@]}"; do say "left for you: $_i"; done
  fi
  if [ "$_rc" -ne 0 ] || [ "$_stage_no" -lt "$TOTAL_STAGES" ]; then
    warn "Stopped during stage $_stage_no of $TOTAL_STAGES (exit $_rc). Run it again to carry on."
  fi
  note "Read a keychain item: security find-generic-password -a \"\$USER\" -s <ITEM> -w"
  note "Use 1Password items in a command: op run --env-file <file with op:// references> -- <command>"
}

_wizard_run() {
  if [ ! -t 0 ]; then
    printf 'This wizard asks you questions, so run it yourself in a terminal: bash %s\n' "$0" >&2
    exit 2
  fi
  trap '_summary $?' EXIT
  trap 'exit 130' INT
  printf '\n%s%s%s\n' "$_b" "$WIZARD_TITLE" "$_r"
  if [ -n "$WIZARD_ABOUT" ]; then say "$WIZARD_ABOUT"; fi
  note "$TOTAL_STAGES stages. Stop with Ctrl-C at any point; run it again to carry on."
  pause "Press Enter to start."
  main "$@"
}

# ===== STAGES: write the stages below this line =====

WIZARD_TITLE="EXAMPLE: replace this title"
WIZARD_ABOUT="EXAMPLE: one line on what this wizard does and what to have open."
TOTAL_STAGES=1

main() {
  stage "EXAMPLE: replace this stage"
  open_url "https://example.com/EXAMPLE"
  step "EXAMPLE: say exactly what to click."
  keychain_store EXAMPLE_API_KEY "the EXAMPLE API key"
}

_wizard_run "$@"
