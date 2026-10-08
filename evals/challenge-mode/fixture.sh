#!/bin/bash
PY=$(command -v python3 || command -v python)
"$PY" -c "import sqlite3,sys; c=sqlite3.connect('growth_memory.db'); c.executescript(open(sys.argv[1],encoding='utf-8').read()); c.commit()" "$(dirname "$0")/../fixtures/growth_memory_v7.sql"
