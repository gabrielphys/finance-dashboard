#!/bin/sh
# Rigenera prezzi e output della dashboard (lanciare da scripts/). Usato anche da GitHub Actions.
set -e
python3 fetch.py >/dev/null; python3 fetch5.py >/dev/null
for s in build opt pac dip2; do python3 $s.py >/dev/null; done
date -u +%Y-%m-%dT%H:%M:%SZ | sed 's/.*/{"updated":"&"}/' > ../data/out/meta.json
