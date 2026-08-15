import sys
import requests
import re

sys.stdout.reconfigure(encoding='utf-8')

r = requests.get('http://127.0.0.1:8001/attack')
print('HTTP status:', r.status_code)

options = re.findall(r'<option[^>]*>(.*?)</option>', r.text, re.DOTALL)
print("\n--- ALL RENDERED OPTIONS IN ATTACK LAB PAGE ---")
for opt in options:
    clean = ' '.join(opt.split())
    if clean and not clean.startswith('-- Select'):
        print("  -", clean)
