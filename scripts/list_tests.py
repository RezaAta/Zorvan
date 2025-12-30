import glob

files = glob.glob("Tests/test_*.py") + glob.glob("Tests/**/*.py", recursive=True)
files = sorted(set(files))
for f in files:
    print(f)
