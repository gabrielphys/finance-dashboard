#!/bin/sh
# Dopo aver copiato i nuovi export XTB in data/xtb_exports/ (EUR_INVEST.xlsx, EUR_LIQUID.xlsx):
# aggiorna lo snapshot del conto e pubblica. Poi aggiornare EXP in build.py/opt.py con la data dell'export.
set -e
cd "$(dirname "$0")"
python3 load.py && ./run_all.sh
cd .. && git add -A && git commit -qm "Aggiorna conto da export XTB" && git push
