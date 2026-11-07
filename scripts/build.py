import json, numpy as np, pandas as pd, datetime as dt
exec(open('load.py').read())
END=pd.offsets.BDay().rollback(pd.Timestamp.now().normalize())   # data di riferimento dell'analisi
EXP=pd.Timestamp('2026-10-30')   # data degli export XTB: posizioni e liquidità sono quelle di questo giorno
# ---- prices in EUR
def series(t):
    d=json.load(open(f'../data/prices/{t}.json'))
    s=pd.Series(d['c'],index=pd.to_datetime(d['ts'],unit='s').normalize()).dropna()
    s=s[~s.index.duplicated(keep='last')]
    return s,d['cur']
fxu,_=series('EURUSD=X'); fxg,_=series('EURGBP=X')
days=pd.bdate_range('2024-10-01',END)
fxu=fxu.reindex(days).ffill().bfill(); fxg=fxg.reindex(days).ffill().bfill()
def eur(t):
    s,c=series(t); s=s.reindex(days).ffill()
    if c=='USD': s=s/fxu
    elif c=='GBp': s=s/100/fxg
    elif c=='GBP': s=s/fxg
    return s
lots=[]
cl=closed[closed.Category!='CFD']
for _,r in cl.iterrows():
    lots.append(dict(t=r.Ticker,vol=float(r.Volume),o=pd.Timestamp(r['Open Time (UTC)']).normalize(),c=pd.Timestamp(r['Close Time (UTC)']).normalize(),pv=float(r['Purchase Value']),sv=float(r['Sale Value'])))
ob=opn[opn.Type=='BUY']
for _,r in ob.iterrows():
    lots.append(dict(t=r.Ticker,vol=float(r.Volume),o=pd.Timestamp(r['Open time (UTC)']).normalize(),c=None,pv=float(r.Value)-float(r['Gross Profit']),now=float(r.Value)))
PX={t:eur(t) for t in set(l['t'] for l in lots)}
# unit scale per ticker: XTB purchase value vs yahoo value at open day
scale={}
for t in PX:
    rs=[l['pv']/(l['vol']*PX[t].asof(l['o'])) for l in lots if l['t']==t and l['vol']>0]
    m=np.median(rs); scale[t]=10**round(np.log10(m)) if abs(np.log10(m))>0.5 else 1.0
print({k:v for k,v in scale.items() if v!=1})
grid=pd.bdate_range('2026-06-05',END)
hold=pd.Series(0.0,index=grid)
for l in lots:
    p=PX[l['t']]*scale[l['t']]
    for d in grid:
        if l['o']<=d and (l['c'] is None or d<l['c']):
            hold[d]+=l['vol']*p.asof(d)
roll=lambda t: float(PX[t].asof(END)/PX[t].asof(EXP))   # valore export portato a END con i prezzi Yahoo
hold[END]=sum(l['now']*roll(l['t']) for l in lots if l['c'] is None)
c=cash.copy(); c['d']=pd.to_datetime(c.Time).dt.normalize(); c.Amount=c.Amount.astype(float)
cashbal=c.groupby('d').Amount.sum().reindex(pd.date_range('2026-06-01',END),fill_value=0).cumsum().reindex(grid,method='ffill')
dep=c[c.Type.isin(['Deposit','Withdrawal'])].groupby('d').Amount.sum()
flow=dep.reindex(pd.date_range('2026-06-01',END),fill_value=0)
# map weekend flows to next business day
flow_b=pd.Series(0.0,index=grid)
for d,v in flow[flow!=0].items(): flow_b[grid[grid>=d][0]]+=v
netdep=flow_b.cumsum()
eq=hold+cashbal
twr=[1.0]
for i in range(1,len(grid)):
    base=eq.iloc[i-1]+flow_b.iloc[i]
    twr.append(twr[-1]*(eq.iloc[i]/base))
twr=pd.Series(twr,index=grid)
# first day: equity vs deposit
twr=twr*(eq.iloc[0]/flow_b.iloc[0])
bm=PX.get('VWCE.DE', eur('VWCE.DE')).reindex(grid).ffill()
bmi=bm/bm.iloc[0]*100
# rebase bench to first-day close relative to deposit: use first day close as 100 and twr index *100
dd=twr/twr.cummax()-1
equity=[dict(day=d.strftime('%Y-%m-%d'),equity=round(eq[d],2),invested=round(hold[d],2),cash=round(cashbal[d],2),net_deposits=round(netdep[d],2),pnl=round(eq[d]-netdep[d],2),twr_index=round(twr[d]*100,3),bench_index=round(bmi[d],3),drawdown=round(dd[d],5)) for d in grid]
print(equity[-1], 'hold check',hold[END], cashbal[END])
# ---- realized stats
rp=twr.pct_change().dropna()
rb=bm.pct_change().dropna()
rf=0.02
def mdd(x): return float((x/x.cummax()-1).min())
# XIRR
flows=[(d,-v) for d,v in flow_b[flow_b!=0].items()]+[(END,eq[END])]
def npv(r): return sum(v/(1+r)**((d-flows[0][0]).days/365) for d,v in flows)
lo,hi=-0.99,10
for _ in range(200):
    m=(lo+hi)/2
    if npv(m)>0: lo=m
    else: hi=m
xirr=m
# ---- ex-ante from current holdings
cur=opn[opn.Type==''].groupby('Ticker').agg(name=('Instrument/Position','first'),cat=('Category','first'),value=('Value','sum'),pnl=('Net Profit','sum'),vol=('Volume','sum'),product=('Product','first')).reset_index()
cur['value']=cur.value.astype(float); cur['pnl']=cur.pnl.astype(float); cur['cost']=cur.value-cur.pnl
cur['value']=cur.value*cur.Ticker.map(roll); cur['pnl']=cur.value-cur.cost
cashnow=float(cashbal[END]); tot=cur.value.sum()+cashnow
cur['weight']=cur.value/tot
y1=pd.bdate_range(END-pd.Timedelta(days=365),END)
R=pd.DataFrame({t:(PX[t]*1).reindex(y1).ffill().pct_change() for t in cur.Ticker})
R['__B']=bm.reindex(y1).ffill().pct_change() if False else eur('VWCE.DE').reindex(y1).ffill().pct_change()
R=R.iloc[1:]
# SPCX short history: fill missing with NaN -> use pairwise; fill with 0 for portfolio sim
w=cur.set_index('Ticker').weight.astype(float)
Rp=R[w.index].fillna(0)
port=(Rp*w).sum(axis=1)
cov=R[w.index].cov()*252
cov=cov.fillna(0)
sig=float(np.sqrt(w.values@cov.values@w.values))
mrc=(cov.values@w.values)*w.values/sig
B=R['__B']
def beta(x):
    m=x.notna()&B.notna(); return float(np.cov(x[m].values,B[m].values)[0,1]/B[m].var())
cur['vol_ann']=[float(R[t].std()*np.sqrt(252)) for t in cur.Ticker]
cur['beta']=[beta(R[t]) for t in cur.Ticker]
cur['ret_1y']=[float((1+R[t].dropna()).prod()-1) for t in cur.Ticker]
cur['risk_share']=mrc/sig
cur['ret_pct']=cur.pnl/cur.cost
var95=float(-np.percentile(port,5)); cvar=float(-port[port<=np.percentile(port,5)].mean())
pidx=(1+port).cumprod()
risk=dict(
 equity=round(eq[END],2), net_deposits=round(netdep[END],2), pnl=round(eq[END]-netdep[END],2),
 twr=round(twr[END]-1,5), bench_ret=round(bmi[END]/100-1,5), xirr=round(xirr,4),
 vol_real=round(float(rp.std()*np.sqrt(252)),4), sharpe_real=round(float((rp.mean()*252-rf)/(rp.std()*np.sqrt(252))),2),
 sortino_real=round(float((rp.mean()*252-rf)/(rp[rp<0].std()*np.sqrt(252))),2),
 maxdd_real=round(mdd(twr),4), best_day=round(float(rp.max()),4), worst_day=round(float(rp.min()),4),
 days=len(grid), start=grid[0].strftime('%Y-%m-%d'), end=END.strftime('%Y-%m-%d'),
 vol_exante=round(sig,4), beta_exante=round(float(np.cov(port.values,B.fillna(0).values)[0,1]/B.var()),2),
 var95_1d=round(var95,4), cvar95_1d=round(cvar,4), var95_1d_eur=round(var95*tot,2),
 maxdd_1y=round(mdd(pidx),4), ret_1y_sim=round(float(pidx.iloc[-1]-1),4),
 bench_vol=round(float(B.std()*np.sqrt(252)),4),
 cash=round(cashnow,2), positions=int(len(cur)), top3=round(float(cur.weight.nlargest(3).sum()),4),
 hhi=round(float((cur.weight**2).sum()),4),
 pac_monthly=round(float(netdep[END]/((END-grid[0]).days/30.44)),0), rf=rf)
risk['corr_bench']=round(float(np.corrcoef(port.values,B.fillna(0).values)[0,1]),2)
print(risk)
pos=[dict(ticker=r.Ticker,name=r['name'],category=r['cat'],product=r['product'].replace('Investment Plans','Investment Plan'),value=round(r.value,2),cost=round(r.cost,2),pnl=round(r.pnl,2),ret_pct=round(r.ret_pct,4),weight=round(r.weight,4),vol_ann=round(r.vol_ann,4),beta=round(r.beta,2),ret_1y=round(r.ret_1y,4),risk_share=round(r.risk_share,4)) for _,r in cur.sort_values('value',ascending=False).iterrows()]
# correlation top 10
top=cur.nlargest(10,'value').Ticker.tolist()
C=R[top].corr()
corr=[dict(a=a,b=b,rho=round(float(C.loc[a,b]),3)) for a in top for b in top]
# monthly flows
c['month']=c.d.dt.strftime('%Y-%m')
grp=lambda types: c[c.Type.isin(types)].groupby('month').Amount.sum()
months=sorted(c.month.unique())
cl2=closed.copy(); cl2['month']=pd.to_datetime(cl2['Close Time (UTC)']).dt.strftime('%Y-%m')
real=cl2.groupby('month')['Profit/Loss'].sum()
ms=pd.DataFrame(index=months)
ms['deposits']=grp(['Deposit','Withdrawal']); ms['bought']=-grp(['Stock purchase']); ms['sold']=grp(['Stock sell'])
ms['income']=grp(['Dividend','Free funds interest']); ms['costs']=grp(['Withholding tax','Tax IFTT','SEC fee','Stamp duty','Free funds interest tax'])
ms['realized']=real
ms=ms.fillna(0).round(2)
flows_m=[dict(month=m,**{k:float(v) for k,v in ms.loc[m].items()}) for m in months]
# realized by instrument
rz=closed.groupby(['Ticker','Instrument','Category']).agg(pnl=('Profit/Loss','sum'),trades=('Profit/Loss','size'),wins=('Profit/Loss',lambda x:(x>0).sum())).reset_index().sort_values('pnl')
realized=[dict(ticker=r.Ticker,name=r.Instrument,category=r.Category,pnl=round(float(r.pnl),2),trades=int(r.trades),wins=int(r.wins)) for _,r in rz.iterrows()]
pl=closed['Profit/Loss'].astype(float)
risk.update(realized_total=round(float(pl.sum()),2),trades_closed=int(len(pl)),win_rate=round(float((pl>0).mean()),4),avg_win=round(float(pl[pl>0].mean()),2),avg_loss=round(float(pl[pl<0].mean()),2),
 dividends=round(float(grp(['Dividend']).sum()),2),interest=round(float(grp(['Free funds interest']).sum()),2),costs_total=round(float(ms.costs.sum()),2),
 unrealized=round(float(cur.pnl.sum()),2))
risk['profit_factor']=round(float(pl[pl>0].sum()/-pl[pl<0].sum()),2)
scen=[dict(scenario='Prudente',mu=0.04,sigma=round(sig*0.85,4),note='Rendimento atteso 4%/anno'),dict(scenario='Base',mu=0.065,sigma=round(sig,4),note='Rendimento atteso 6,5%/anno'),dict(scenario='Ottimista',mu=0.09,sigma=round(sig*1.1,4),note='Rendimento atteso 9%/anno')]
alloc=[]
for k,g in cur.groupby('cat'): alloc.append(dict(group='Asset class',label=k,value=round(float(g.value.sum()),2)))
alloc.append(dict(group='Asset class',label='CASH',value=round(cashnow,2)))
for k,g in cur.groupby('product'): alloc.append(dict(group='Strategia',label=k.replace('Investment Plans','Investment Plan'),value=round(float(g.value.sum()),2)))
os.makedirs('../data/out',exist_ok=True) if False else None
import os; os.makedirs('../data/out',exist_ok=True)
for n,o in dict(equity=equity,risk=[risk],positions=pos,corr=corr,flows=flows_m,realized=realized,scenarios=scen,allocation=alloc).items():
    json.dump(o,open(f'../data/out/{n}.json','w'),ensure_ascii=False)
print(pd.DataFrame(pos)[['ticker','value','weight','vol_ann','beta','risk_share']].to_string())
print(flows_m)
