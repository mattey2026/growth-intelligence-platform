#!/usr/bin/env python3
"""
build_fixtures.py: rebuilds the binary test fixtures from their readable text sources.

The repository stores test data as readable text so that every file can be reviewed:
  *.sql             → SQLite databases (*.db)       (complete SQL dump: schema + rows)
  *.workbook.json   → Excel workbooks (*.xlsx)      (one table per sheet, with column types)
The generated binaries are git-ignored. Every test runner calls ensure() first; it is idempotent and fast.
USAGE: python tests/fixtures/build_fixtures.py [--force]     (or import and call ensure())
"""
import glob, json, os, sqlite3, sys
HERE = os.path.dirname(os.path.abspath(__file__))
def build_db(sql_path, db_path):
    tmp = db_path + ".tmp"
    if os.path.exists(tmp): os.remove(tmp)
    con = sqlite3.connect(tmp); con.executescript(open(sql_path, encoding="utf-8").read()); con.commit(); con.close()
    os.replace(tmp, db_path)
def build_xlsx(json_path, xlsx_path):
    import pandas as pd
    from io import StringIO
    spec = json.load(open(json_path, encoding="utf-8"))
    tmp = xlsx_path + ".tmp.xlsx"
    with pd.ExcelWriter(tmp, engine="openpyxl") as w:
        for sheet in spec["sheets"]:
            df = pd.read_json(StringIO(json.dumps(sheet["table"])), orient="table")
            df.to_excel(w, sheet_name=sheet["name"], index=False)
    os.replace(tmp, xlsx_path)
def ensure(force=False, folder=HERE):
    built = []
    for s in glob.glob(os.path.join(folder, "*.sql")):
        d = s[:-4] + ".db"
        if force or not os.path.exists(d) or os.path.getmtime(d) < os.path.getmtime(s): build_db(s, d); built.append(os.path.basename(d))
    for j in glob.glob(os.path.join(folder, "*.workbook.json")):
        x = j[:-len(".workbook.json")] + ".xlsx"
        if force or not os.path.exists(x) or os.path.getmtime(x) < os.path.getmtime(j): build_xlsx(j, x); built.append(os.path.basename(x))
    return built
if __name__ == "__main__":
    folders = [HERE] + [a for a in sys.argv[1:] if not a.startswith("--")]
    for f in folders: print(f, "→", ensure("--force" in sys.argv, f) or "up to date")
