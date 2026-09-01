cd /root/byd23-toast-hygiene
grep -o ".cat-title{[^}]*}" index.html | cut -c1-160
grep -o ".cat-section{[^}]*}" index.html | cut -c1-120