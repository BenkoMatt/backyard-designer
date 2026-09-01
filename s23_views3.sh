cd /root/byd23-toast-hygiene
echo "== verdict tail of each surface (latest run) =="
cd reports/sprint23_shots
for f in v_main_basic v_sidebar_advanced v_toolbar_panel_basic v_underground_advanced v_help_modal_basic; do
  echo "--- $f"
  grep -i "^verdict\|verdict:" $f.verdict.txt | tail -1
  tail -2 $f.verdict.txt | head -1
done