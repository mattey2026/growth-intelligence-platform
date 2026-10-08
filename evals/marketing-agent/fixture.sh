#!/bin/bash
F="$(dirname "$0")/../fixtures"
cp "$F/growth_memory_v7.db" ./growth_memory.db
for f in sanofi_marketing_SYNTHETIC.json sanofi_contacts_SYNTHETIC.json sanofi_opps_SYNTHETIC.json sanofi_campaigns_SYNTHETIC.json sanofi_initiatives.json; do cp "$F/$f" .; done
