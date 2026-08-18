import json
from pathlib import Path
p = Path('graphify-out/.graphify_detect.json')
d = json.loads(p.read_text(encoding='utf-8'))
dropped = [f for f in d['files'].get('code', []) if f.endswith('saudi-local-db.json')]
d['files']['code'] = [f for f in d['files'].get('code', []) if not f.endswith('saudi-local-db.json')]
d['total_files'] = sum(len(v) for v in d['files'].values())
d['total_words'] = 76341
p.write_text(json.dumps(d, ensure_ascii=False), encoding='utf-8')
print('dropped:', dropped)
print('total_files now', d['total_files'], {k: len(v) for k, v in d['files'].items()})
