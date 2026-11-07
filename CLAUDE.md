# Financial Analysis – progetto portafoglio XTB

Contesto di lavoro per l'analisi quantitativa del portafoglio personale di [titolare] su XTB. Questa è analisi, non una raccomandazione d'investimento.

## Struttura
- `scripts/` – pipeline Python (pandas, numpy, openpyxl, scipy se richiesto):
  - `load.py` legge gli export XTB (`.xlsx`) in `data/xtb_exports/`.
  - `fetch.py` / `fetch5.py` scaricano i prezzi giornalieri da Yahoo Finance in `data/prices/`.
  - `build.py` calcola patrimonio, TWR, rischio, flussi, posizioni e scrive in `data/out/`.
  - `opt.py`, `pac.py`, `fit.py`, `gold.py` ottimizzazione, piani PAC, stima e oro.
  - `dip.py`, `dip2.py` backtest sulle ricariche (PAC A/C su calo del Nasdaq 100).
- `data/out/` – output JSON usati dalla dashboard (`xtb_*_u30.json` = versioni al 30/10/2026).
- ``index.html` – dashboard (pagina statica, dati incorporati).

## Come riprodurre l'analisi
Tutti gli script vanno lanciati **dalla cartella `scripts/`** (percorsi relativi a `../data/`).
Dipendenze: `pip3 install pandas numpy openpyxl scipy scikit-learn`.
1. Copiare i nuovi export XTB in `data/xtb_exports/` rinominandoli `EUR_INVEST.xlsx` e `EUR_LIQUID.xlsx` (nomi fissi letti da `load.py`).
2. Aggiornare `END` (data dell'analisi, ora `2026-11-06`) ed `EXP` (data degli export XTB, ora `2026-10-30`) in `build.py` e `opt.py`. Se `END` > `EXP` le posizioni dell'export sono valorizzate ai prezzi di `END` (anche in `pac.py`); la liquidità resta quella dell'export.
3. `python3 fetch.py` (prezzi da 10/2024 → `data/prices/`) e `python3 fetch5.py` (prezzi da 2021 → `data/prices5/`, lista simboli di default nello script).
4. `build.py`, poi `opt.py`, `pac.py`, `dip2.py`. Facoltativi: `gold.py` (sensibilità oro), `fit.py` (→ `xtb_fit.json`).
5. Aggiornare i dataset della dashboard con i nuovi file di `data/out/`.

## Conti e piani
- Conto investimenti XTB (EUR) e conto liquidità collegato.
- Tre PAC: A (World + Nasdaq), B (multi-fattore), C (ribilanciamento + oro e small cap value).
- Stato al 30/10/2026: PAC A e B in pausa; PAC C attivo e alimentato dal sub-conto dedicato.

## Profilo e obiettivi (dichiarati dall'utente)
- Rischio desiderato 7,5/10, orizzonte di 5 anni.
- Obiettivo di allocazione "Ottimale + Oro".
- Liquidità da far crescere in parallelo, con peso minore rispetto agli investimenti.

## Convenzioni
- Valute convertite in EUR con EURUSD/EURGBP da Yahoo.
- Liquidità remunerata ipotizzata al 2% lordo, tassazione 26%.
- Dati storici sempre datati; indicare la data di riferimento in ogni output.
