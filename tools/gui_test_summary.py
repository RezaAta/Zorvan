import pathlib, re
base = pathlib.Path('Tests/gui_tests')
for sub in ['unit', 'integration']:
    p = base / sub
    print(f'=== {sub} ===')
    for f in sorted([f for f in p.iterdir() if f.suffix == '.py']):
        text = f.read_text(encoding='utf-8', errors='replace')
        lines = text.splitlines()
        first = [l for l in lines[:40] if l.strip()]
        first20 = '\n'.join(first[:8])
        defs = re.findall(r'^(?:async\s+)?def\s+(test_[A-Za-z0-9_]+)\s*\(', text, re.MULTILINE)
        classes = re.findall(r'^class\s+([A-Za-z0-9_]+)\s*\(?', text, re.MULTILINE)
        print(f'{f.name}')
        print('--- top lines ---')
        print(first20)
        if classes:
            print('classes:', ', '.join(classes[:8]))
        if defs:
            print('tests:', ', '.join(defs[:10]) + ('...' if len(defs) > 10 else ''))
        print()