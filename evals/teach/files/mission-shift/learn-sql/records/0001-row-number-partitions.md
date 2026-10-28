# 0001 ROW_NUMBER and partitions
<!-- DEMO FIXTURE: invented learner and data, for skill trials only. -->

Date: 2026-10-21
Lesson: lessons/0001-row-number-partitions.html

## What stuck
PARTITION BY restarts the numbering for each group; ROW_NUMBER numbers rows in the OVER order.

## Evidence
Quiz 4 of 5. Rewrote the top-customers query from memory with the partition on region only.

## Still shaky
The ORDER BY inside OVER versus the ORDER BY at the end of the query.

## Next
Ties: rank and dense_rank against row_number.
