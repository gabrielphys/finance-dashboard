import openpyxl, warnings, pandas as pd
warnings.filterwarnings('ignore')
B='../data/xtb_exports/'
F=[B+'EUR_INVEST.xlsx',B+'EUR_LIQUID.xlsx']
def sheet(f,name,hdr_row):
    ws=openpyxl.load_workbook(f,data_only=True)[name]
    rows=list(ws.iter_rows(values_only=True))
    hdr=rows[hdr_row]; data=[r for r in rows[hdr_row+1:] if r[0] not in (None,'Total','Profit/loss')]
    return pd.DataFrame(data,columns=hdr)
import os, pickle
SNAP='../data/snapshot.pkl'   # copia dei dati conto dall'ultimo export XTB (senza numeri di conto): usata quando gli .xlsx non ci sono (es. GitHub Actions)
if all(os.path.exists(f) for f in F):
    cash=pd.concat([sheet(f,'Cash Operations',4).assign(acct=f.split('_')[-1][:-5]) for f in F])
    closed=pd.concat([sheet(f,'Closed Positions',4).assign(acct=f.split('_')[-1][:-5]) for f in F])
    op=[]
    for f in F:
        ws=openpyxl.load_workbook(f,data_only=True)['Open Positions']
        rows=list(ws.iter_rows(values_only=True))
        i=[k for k,r in enumerate(rows) if r[1]=='Instrument/Position'][0]
        df=pd.DataFrame([r for r in rows[i+1:] if r[0]],columns=rows[i]); op.append(df)
    opn=pd.concat(op)
    cash['Comment']=cash['Comment'].astype(str).str.replace(r'\b\d{8}\b','[CONTO]',regex=True)   # numeri di conto nei commenti dei trasferimenti
    pickle.dump((cash,closed,opn),open(SNAP,'wb'))
else:
    cash,closed,opn=pickle.load(open(SNAP,'rb'))
