#!/bin/bash
F="$(dirname "$0")/../fixtures"
cp "$F/growth_memory_v7.db" ./growth_memory.db
for f in sanofi_financials_PUBLIC.json sanofi_events_PUBLIC.json; do cp "$F/$f" .; done
