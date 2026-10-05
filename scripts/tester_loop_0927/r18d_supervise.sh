#!/bin/zsh
# R18D 监督循环：exit 10=预算耗尽可续 → 重拉；0=达标停；2=阻断停（交人工判）
cd "$(dirname "$0")"
typeset -i rounds=0
while true; do
  python3 r18d_seed_csu.py >> r18d_seed_console.log 2>&1
  rc=$?
  rounds+=1
  echo "[supervisor $(date -u +%H:%M:%SZ)] round $rounds exit=$rc" >> r18d_seed_console.log
  if [ $rc -eq 0 ]; then echo "[supervisor] DONE" >> r18d_seed_console.log; break; fi
  if [ $rc -ne 10 ]; then echo "[supervisor] STOP rc=$rc" >> r18d_seed_console.log; break; fi
  sleep 300
done
