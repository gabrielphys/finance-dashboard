import openpyxl, warnings, pandas as pd
warnings.filterwarnings('ignore')
B='../data/xtb_exports/'
F=[B+'EUR_INVEST.xlsx',B+'EUR_LIQUID.xlsx']
def sheet(f,name,hdr_row):
    ws=openpyxl.load_workbook(f,data_only=True)[name]
    rows=list(ws.iter_rows(values_only=True))
    hdr=rows[hdr_row]; data=[r for r in rows[hdr_row+1:] if r[0] not in (None,'Total','Profit/loss')]
    return pd.DataFrame(data,columns=hdr)
cash=pd.concat([sheet(f,'Cash Operations',4).assign(acct=f.split('_')[-1][:-5]) for f in F])
closed=pd.concat([sheet(f,'Closed Positions',4).assign(acct=f.split('_')[-1][:-5]) for f in F])
op=[]
for f in F:
    ws=openpyxl.load_workbook(f,data_only=True)['Open Positions']
    rows=list(ws.iter_rows(values_only=True))
    i=[k for k,r in enumerate(rows) if r[1]=='Instrument/Position'][0]
    df=pd.DataFrame([r for r in rows[i+1:] if r[0]],columns=rows[i]); op.append(df)
opn=pd.concat(op)
