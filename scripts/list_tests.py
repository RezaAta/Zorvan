import glob

files = glob.glob("reference/Tests/test_*.py") + glob.glob("reference/Tests/**/*.py", recursive=True)
files = sorted(set(files))
for f in files:
    print(f)
