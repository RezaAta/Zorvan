from zorvan.GUI.node_registry import get_node_categories

cats = get_node_categories()
print("categories count:", len(cats))
print("some keys:", list(cats.keys())[:10])
for k in list(cats.keys())[:10]:
    print("-", k)
