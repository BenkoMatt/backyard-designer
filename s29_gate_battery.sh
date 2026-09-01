#!/bin/bash
# Sprint 29 Agent 4 — final gate battery (all against my server on 8191)
cd /root/byd29-audit-transients
P=8191
echo "===== sprint11 (143 expected) ====="
timeout 400 python3 sprint11_quality_gate.py --port $P 2>&1 | tail -4
echo "===== sprint15 (52 expected) ====="
timeout 400 python3 sprint15_quality_gate.py --port $P 2>&1 | tail -4
echo "===== sprint17 (81 expected) ====="
timeout 400 BASE_URL=http://localhost:$P python3 sprint17_quality_gate.py 2>&1 | tail -4
echo "===== sprint21 (55 expected) ====="
timeout 400 python3 sprint21_quality_gate.py --port $P 2>&1 | tail -4
echo "===== sprint22 (43 expected) ====="
timeout 400 python3 sprint22_quality_gate.py --port $P 2>&1 | tail -4
echo "===== qa_s21 (16 expected) ====="
timeout 300 BASE_URL=http://localhost:$P python3 qa_s21_dig_visibility.py 2>&1 | tail -4
echo "===== sprint23 (24/24 REQUIRED incl V03 toast lock) ====="
timeout 500 python3 sprint23_quality_gate.py --port $P 2>&1 | tail -6
echo "===== size_budget (4/4) ====="
python3 size_budget.py 2>&1 | tail -2
echo "===== sprint16 (informational, 29/32 expected pre-existing) ====="
timeout 400 BASE_URL=http://localhost:$P python3 sprint16_quality_gate.py 2>&1 | tail -4
echo "BATTERY_DONE"