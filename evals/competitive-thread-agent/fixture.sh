#!/bin/bash
F="$(dirname "$0")/../fixtures"
cp "$F/growth_memory_v7.db" ./growth_memory.db
for f in sanofi_competitor_signals_SYNTHETIC.json; do cp "$F/$f" .; done
