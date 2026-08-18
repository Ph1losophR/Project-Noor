import json, os
from pathlib import Path
from collections import Counter
d = json.loads(Path('graphify-out/.graphify_detect.json').read_text(encoding='utf-8'))
root = d['scan_root']
c = Counter()
for cat, fl in d['files'].items():
    for f in fl:
        rel = os.path.relpath(f, root).replace(os.sep, '/')
        top = rel.split('/')[0] if '/' in rel else '(root)'
        c[top] += 1
        try:
            w = len(Path(f).read_text(encoding='utf-8', errors='ignore').split())
        except Exception:
            w = -1
        print(f'{cat:9} {w:>10,}  {rel}')
print()
for k, v in c.most_common():
    print(k, v)
