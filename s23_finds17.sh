cd /root/byd23-toast-hygiene
L=$(grep -n "hiddenInBasic" index.html | head -1 | cut -d: -f1)
echo "line $L"
awk -v s=$L 'NR>=s-3 && NR<=s+8' index.html