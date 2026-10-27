#!/usr/bin/env bash
# DEMO MATERIAL for a skill trial. Builds the weekly sales report from sales.csv.
set -euo pipefail
cd "$(dirname "$0")"
awk -F, 'NR>1 {t+=$2} END {printf "Total sales: %.2f\n", t}' sales.csv > report.txt
echo "wrote report.txt"
