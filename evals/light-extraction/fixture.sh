#!/bin/bash
# Copies the shared two-review test memory into the empty run workspace (needs --scaffold)
cp "$(dirname "$0")/../fixtures/growth_memory_test.db" ./growth_memory.db
