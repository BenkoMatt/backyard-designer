#!/bin/bash
# Sprint 23 Agent 3 — final gate battery (all gates against port 8095)
cd /root/byd23-toast-hygiene
echo "===== sprint15 ====="
python3 sprint15_quality_gate.py --port 8095 2>&1 | tail -3
echo "===== sprint17 ====="
python3 sprint17_quality_gate.py --port 8095 2>&1 | tail -3
echo "===== sprint21 ====="
python3 sprint21_quality_gate.py --port 8095 2>&1 | tail -3
echo "===== sprint22 ====="
python3 sprint22_quality_gate.py --port 8095 2>&1 | tail -3
echo "===== qa_s21_dig_visibility ====="
BASE_URL=http://localhost:8095 python3 qa_s21_dig_visibility.py 2>&1 | tail -3