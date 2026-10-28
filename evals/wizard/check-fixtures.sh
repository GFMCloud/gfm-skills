#!/bin/sh
# Builds the wizard checker's demo fixtures in a temporary folder from the current template, then
# checks them: good.sh and ok-*.sh must PASS with no WARN, warn-*.sh must PASS with a WARN,
# bad-*.sh must FAIL. Run from anywhere: sh evals/wizard/check-fixtures.sh
HERE=$(cd "$(dirname "$0")" && pwd)
CHECK="$HERE/../../skills/wizard/scripts/check_wizard.py"
OUT=$(mktemp -d) || exit 2
trap 'rm -rf "$OUT"' EXIT
python3 "$HERE/rebuild-checker-fixtures.py" "$OUT" > /dev/null || exit 2
cd "$OUT" || exit 2
n=0; bad=0
for f in good.sh ok-*.sh warn-*.sh bad-*.sh; do
  n=$((n + 1))
  out=$(python3 "$CHECK" "$f" --ci workflows 2>&1); rc=$?
  warns=$(printf '%s\n' "$out" | grep -c '^WARN')
  case $f in
    bad-*)  ok=$([ "$rc" = 1 ] && echo y) ;;
    warn-*) ok=$([ "$rc" = 0 ] && [ "$warns" -gt 0 ] && echo y) ;;
    *)      ok=$([ "$rc" = 0 ] && [ "$warns" = 0 ] && echo y) ;;
  esac
  if [ "$ok" = y ]; then echo "ok   $f (exit $rc, $warns warn)"
  else echo "FAIL $f (exit $rc, $warns warn)"; printf '%s\n' "$out" | grep -E '^(WARN|FAIL)' | sed 's/^/     /'; bad=$((bad + 1)); fi
done
echo "$((n - bad)) of $n fixtures as expected"
[ "$bad" = 0 ]
