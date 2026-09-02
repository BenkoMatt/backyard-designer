#!/bin/bash
cd /root/byd23-toast-hygiene
mv reports/sprint23_shots/v_main_basic.verdict.txt reports/sprint23_shots/v_main_basic.verdict.txt.prev 2>/dev/null
mv reports/sprint23_shots/v_sidebar_advanced.verdict.txt reports/sprint23_shots/v_sidebar_advanced.verdict.txt.prev 2>/dev/null
mv reports/sprint23_shots/v_toolbar_panel_basic.verdict.txt reports/sprint23_shots/v_toolbar_panel_basic.verdict.txt.prev 2>/dev/null
mv reports/sprint23_shots/v_underground_advanced.verdict.txt reports/sprint23_shots/v_underground_advanced.verdict.txt.prev 2>/dev/null
mv reports/sprint23_shots/v_help_modal_basic.verdict.txt reports/sprint23_shots/v_help_modal_basic.verdict.txt.prev 2>/dev/null
python3 sprint23_quality_gate.py --port 8095 2>&1 | tail -5