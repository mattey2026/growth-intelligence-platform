#!/bin/bash
F="$(dirname "$0")/../fixtures"
PY=$(command -v python3 || command -v python)
"$PY" -c "import sqlite3,sys; c=sqlite3.connect('growth_memory.db'); c.executescript(open(sys.argv[1],encoding='utf-8').read()); c.commit()" "$F/growth_memory_v7.sql"
for f in sanofi_competitor_signals_SYNTHETIC.json; do cp "$F/$f" .; done
