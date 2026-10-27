#!/usr/bin/env bash
# Regression checks for the automation skill's helper scripts. Runs in a temporary folder and
# removes nothing outside it. Usage: bash evals/automation/regress.sh   (from the repo root)
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
scripts=$(cd "$here/../../skills/automation/scripts" && pwd)
W="$scripts/watch_state.py"
G="$scripts/loop_gate.py"
tmp=$(mktemp -d)
pass=0
fail=0

expect() {  # expect <name> <expected-prefix> <actual>
  if [[ "$3" == "$2"* ]]; then pass=$((pass + 1)); else fail=$((fail + 1)); echo "FAIL $1: wanted '$2...', got '$3'"; fi
}
code() {  # code <name> <expected-exit> <command...>
  local want=$2; shift 2
  set +e; "$@" >/dev/null 2>&1; local got=$?; set -e
  if [ "$got" = "$want" ]; then pass=$((pass + 1)); else fail=$((fail + 1)); echo "FAIL exit: wanted $want, got $got: $*"; fi
}

# watch_state.py
S="$tmp/w.json"
expect baseline   "BASELINE"  "$(python3 "$W" "$S" src OK)"
expect same       "NO-CHANGE" "$(python3 "$W" "$S" src OK)"
expect change     "REPORT src OK -> DOWN" "$(python3 "$W" "$S" src DOWN)"
expect repeats    "REPORT src OK -> DOWN" "$(python3 "$W" "$S" src DOWN)"
expect confirm    "CONFIRMED src DOWN" "$(python3 "$W" --confirm "$S" src)"
expect quiet      "NO-CHANGE" "$(python3 "$W" "$S" src DOWN)"
expect up         "REPORT src DOWN -> OK" "$(python3 "$W" "$S" src OK)"
expect blip       "REPORT src DOWN -> OK -> DOWN" "$(python3 "$W" "$S" src DOWN)"
expect blip-again "REPORT src DOWN -> OK -> DOWN" "$(python3 "$W" "$S" src DOWN)"
python3 "$W" --confirm "$S" src >/dev/null
expect unread     "REPORT src DOWN -> UNREADABLE (timeout)" "$(python3 "$W" "$S" src --unreadable timeout)"
python3 "$W" --confirm "$S" src >/dev/null
expect unread-q   "NO-CHANGE" "$(python3 "$W" "$S" src --unreadable timeout)"
expect recovered  "REPORT src UNREADABLE -> OK (readable again)" "$(python3 "$W" "$S" src OK)"
python3 "$W" "$tmp/w2.json" src OK >/dev/null
expect nothing    "NOTHING-PENDING" "$(python3 "$W" --confirm "$tmp/w2.json" src)"
code   no-file    2 python3 "$W" --confirm "$tmp/w3.json" src
code   wrong-src  2 python3 "$W" "$S" other OK
code   reserved   2 python3 "$W" "$S" src UNREADABLE
code   hash-mix   2 python3 "$W" --hash "$S" src OK
code   wrong-pend 2 python3 "$W" --confirm "$S" src NOPE
echo '{broken' > "$tmp/bad.json"
code   corrupt    2 python3 "$W" "$tmp/bad.json" src OK
expect untouched  "{broken" "$(cat "$tmp/bad.json")"
H="$tmp/h.json"
expect hash-base  "BASELINE src page one" "$(echo 'page one' | python3 "$W" --hash "$H" src -)"
expect hash-same  "NO-CHANGE" "$(echo 'page one' | python3 "$W" --hash "$H" src -)"
expect hash-chg   "REPORT src page one -> page two" "$(echo 'page two' | python3 "$W" --hash "$H" src -)"
python3 "$W" --confirm "$H" src >/dev/null
expect hash-unread "REPORT src page two -> UNREADABLE (down)" "$(python3 "$W" "$H" src --unreadable down)"

# loop_gate.py
P="$tmp/proj"
mkdir -p "$P/tests"
printf 'def add(a, b):\n    return a - b\n' > "$P/calc.py"
printf 'import sys; sys.path.insert(0, ".")\nfrom calc import add\nassert add(2, 2) == 4\n' > "$P/tests/check.py"
gate() { (cd "$P" && python3 "$G" "$@"); }
code   no-state   1 gate step
code   bad-guard  1 gate init --check "python3 tests/check.py" --guard ../outside
code   init       0 gate init --check "python3 tests/check.py" --guard tests --budget 2
code   fail-1     3 gate step
code   idle       3 gate step
code   no-prog    4 gate step
expect cause      "STOPPED: 1 of 2 attempts used" "$(gate status)"
test -s "$P/.automation/loop/ESCALATION.md" && pass=$((pass + 1)) || { fail=$((fail + 1)); echo "FAIL no ESCALATION.md"; }
gate init --check "python3 tests/check.py" --guard tests --budget 2 >/dev/null
printf 'def add(a, b):\n    return a * b + 1\n' > "$P/calc.py"
code   fail-a     3 gate step
printf 'def add(a, b):\n    return a * b + 2\n' > "$P/calc.py"
code   budget     4 gate step
expect spent      "STOPPED: 2 of 2 attempts used, check" "$(gate status)"
gate init --check "python3 tests/check.py" --guard tests >/dev/null
printf 'def add(a, b):\n    return a + b\n' > "$P/calc.py"
code   pass       0 gate step
code   pass-again 0 gate step
gate init --check "python3 tests/check.py" --guard tests >/dev/null
echo 'print("ok")' > "$P/tests/check.py"
code   guard      4 gate step
expect guard-why  "STOPPED: 0 of 3 attempts used, check" "$(gate status)"
code   hook-show  2 sh -c "echo '{\"cwd\":\"$P\"}' | python3 '$G' step --hook"
code   hook-free  0 sh -c "echo '{\"cwd\":\"$P\"}' | python3 '$G' step --hook"
gate init --check "no-such-tool-xyz" >/dev/null
code   broken     4 gate step
gate init --check "sleep 5" --timeout 1 >/dev/null
echo x > "$P/touch.txt"
code   timeout    3 gate step

# Fixes after the Fable review, round 1
expect bytes-hash "BASELINE src" "$(printf '\xff\xfe\x80abc' | LANG=en_US.UTF-8 python3 "$W" --hash "$tmp/b.json" src -)"
expect bytes-raw  "BASELINE src" "$(printf '\xff\xfe' | LANG=en_US.UTF-8 python3 "$W" "$tmp/b2.json" src -)"
code   nl-source  2 python3 "$W" "$tmp/b3.json" "$(printf 'a\nb')" OK
code   too-long   2 python3 "$W" "$tmp/b4.json" src "$(printf '%01200d' 0)"
mkdir "$tmp/ro"; chmod 555 "$tmp/ro"
code   ro-state   2 python3 "$W" "$tmp/ro/s.json" src OK
chmod 755 "$tmp/ro"
Q="$tmp/q"
mkdir -p "$Q/tests" "$Q/automation/job/state"
echo 'assert False' > "$Q/tests/t.py"
gq() { (cd "$Q" && python3 "$G" "$@"); }
code   empty-chk  1 gq init --check "  "
gq init --check "python3 tests/t.py" --guard tests/t.py --guard automation/job \
  --state automation/job/state/loop.json --budget 5 >/dev/null
code   q-fail-1   3 gq step --state automation/job/state/loop.json
date +%s%N > "$Q/automation/job/state/last-run.txt"
code   q-idle     3 gq step --state automation/job/state/loop.json
date +%s%N > "$Q/automation/job/state/last-run.txt"
code   q-noprog   4 gq step --state automation/job/state/loop.json
expect q-cause    "STOPPED: 1 of 5 attempts used, check" "$(gq status --state automation/job/state/loop.json)"
gq init --check "date > out.txt; exit 1" --ignore out.txt --budget 5 >/dev/null
code   ign-1      3 gq step
code   ign-idle   3 gq step
code   ign-stop   4 gq step
gq init --check "python3 tests/t.py" --guard tests/t.py >/dev/null
chmod 000 "$Q/tests/t.py"
code   unread-g   2 sh -c "echo '{\"cwd\":\"$Q\"}' | python3 '$G' step --hook"
chmod 644 "$Q/tests/t.py"
expect unread-why "STOPPED: 0 of 3 attempts used" "$(gq status)"
gq init --check "echo 'bash: foo: command not found'; exit 1" >/dev/null
code   cnf-text   3 gq step
gq init --check "python3 -c 'print(\"x\" * 3000000)'; exit 1" >/dev/null
code   big-out    3 gq step
size=$(wc -c < "$Q/.automation/loop/state.json")
[ "$size" -lt 100000 ] && pass=$((pass + 1)) || { fail=$((fail + 1)); echo "FAIL state.json is $size bytes"; }
gq init --check "(sleep 3; touch late.txt) & wait" --timeout 1 >/dev/null
code   kill-tree  3 gq step
sleep 3
[ ! -e "$Q/late.txt" ] && pass=$((pass + 1)) || { fail=$((fail + 1)); echo "FAIL timed-out check's child kept running"; }
code   cwd-int    1 sh -c "cd '$tmp' && echo '{\"cwd\":123}' | python3 '$G' step --hook"

rm -rf "$tmp"
echo "$pass passed, $fail failed"
[ "$fail" = 0 ]
