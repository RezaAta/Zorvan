from gui_framework.legacy import ExamplesLoader

loader = ExamplesLoader()
for c in loader.get_categories():
    print(c.name)
    for e in c.examples:
        print(" -", e[0])

print("\nBuild every example:")
for cat in loader.get_categories():
    for name, desc, fn in cat.examples:
        g = fn()
        print(f"  {cat.name} / {name}: {len(g.nodes)} nodes")
