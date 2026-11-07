import json, numpy as np, pandas as pd
from scipy.optimize import minimize, linprog
from sklearn.covariance import LedoitWolf
END=pd.offsets.BDay().rollback(pd.Timestamp.now().normalize()); EXP=pd.Timestamp('2026-10-30')   # analisi / export XTB
def load(sym):
    d=json.load(open(f'../data/prices5/{sym}.json'))
    s=pd.Series(d['c'],index=pd.to_datetime(d['ts'],unit='s').normalize(),dtype=float).dropna()
    return s[~s.index.duplicated(keep='last')],d['cur'],d['name']
days=pd.bdate_range('2021-01-04',END)
fxu=load('EURUSD=X')[0].reindex(days).ffill().bfill(); fxg=load('EURGBP=X')[0].reindex(days).ffill().bfill()
def eur(sym):
    s,c,n=load(sym); s=s.reindex(days).ffill()
    if c=='USD': s=s/fxu
    elif c=='GBp': s=s/100/fxg
    return s
HOLD={'SXRV.DE':'SXRV.DE','VWCE.DE':'VWCE.DE','SPPW.DE':'SPPW.DE','EUNL.DE':'EUNL.DE','XDWD.DE':'XDWD.DE','TPRO.IT':'TPRO.MI','VGWD.DE':'VGWD.DE','IS3S.DE':'IS3S.DE','VDIV.DE':'VDIV.DE','SXRT.DE':'SXRT.DE','SXR8.DE':'SXR8.DE','QDVE.DE':'QDVE.DE','XAIX.DE':'XAIX.DE','SPCX.US':'SPCX','ISP.IT':'ISP.MI','TSLA.US':'TSLA','ISLN.UK':'ISLN.L','ATS.DE':'ATS.VI','STM.IT':'STMMI.MI','RACE.IT':'RACE.MI','PTX.DE':'PTX.DE','MH6.DE':'MH6.F'}
pos=pd.DataFrame(json.load(open('../data/out/positions.json'))); risk=json.load(open('../data/out/risk.json'))[0]
P={t:eur(y) for t,y in HOLD.items()}
CAND=['4GLD.DE','XGLE.DE','EUNA.DE','IBCI.DE','XEON.DE','IQQ0.DE','IS3N.DE','ZPRV.DE','ZPRX.DE','IS3Q.DE','EXXY.DE','DBXG.DE','XDEM.DE','TRET.DE']
for c in CAND: P[c]=eur(c)
R=pd.DataFrame({k:v.pct_change(fill_method=None) for k,v in P.items()}).iloc[1:]
B=R['VWCE.DE']
# fill missing with beta*bench
for k in R:
    m=R[k].notna()&B.notna()
    if R[k].isna().sum()>5:
        b=np.cov(R[k][m],B[m])[0,1]/B[m].var(); R[k]=R[k].fillna(b*B)
R=R.fillna(0)
NAMES={'4GLD.DE':'Xetra-Gold (oro fisico)','XGLE.DE':'Xtrackers Eurozone Govt Bond','EUNA.DE':'iShares Global Aggregate Bond EUR-H','IBCI.DE':'iShares € Inflation Linked Govt','XEON.DE':'Xtrackers EUR Overnight (€STR)','IQQ0.DE':'iShares MSCI World Min Volatility','IS3N.DE':'iShares Core MSCI EM IMI','ZPRV.DE':'SPDR MSCI USA Small Cap Value','ZPRX.DE':'SPDR MSCI Europe Small Cap Value','IS3Q.DE':'iShares MSCI World Quality','EXXY.DE':'iShares Diversified Commodity','DBXG.DE':'Xtrackers Eurozone Govt 25+','XDEM.DE':'Xtrackers MSCI World Momentum','TRET.DE':'VanEck Global Real Estate'}
CLS={'4GLD.DE':'Oro','XGLE.DE':'Obbligazioni','EUNA.DE':'Obbligazioni','IBCI.DE':'Obbligazioni','XEON.DE':'Liquidità','IQQ0.DE':'Azioni fattoriali','IS3N.DE':'Azioni emergenti','ZPRV.DE':'Azioni fattoriali','ZPRX.DE':'Azioni fattoriali','IS3Q.DE':'Azioni fattoriali','EXXY.DE':'Materie prime','DBXG.DE':'Obbligazioni','XDEM.DE':'Azioni fattoriali','TRET.DE':'Immobiliare',
 'SXRV.DE':'Azioni tech','QDVE.DE':'Azioni tech','XAIX.DE':'Azioni tech','VWCE.DE':'Azioni globali','SPPW.DE':'Azioni globali','EUNL.DE':'Azioni globali','XDWD.DE':'Azioni globali','SXR8.DE':'Azioni globali','SXRT.DE':'Azioni Europa','VGWD.DE':'Azioni dividendo','VDIV.DE':'Azioni dividendo','IS3S.DE':'Azioni fattoriali','SAT':'Azioni singole'}
MU={'VWCE.DE':.065,'SPPW.DE':.065,'EUNL.DE':.065,'XDWD.DE':.065,'SXR8.DE':.062,'SXRV.DE':.062,'QDVE.DE':.062,'XAIX.DE':.062,'SXRT.DE':.07,'VGWD.DE':.068,'VDIV.DE':.068,'IS3S.DE':.07,
 'IQQ0.DE':.06,'IS3Q.DE':.065,'ZPRV.DE':.075,'ZPRX.DE':.075,'IS3N.DE':.075,'XDEM.DE':.065,'TRET.DE':.06,'XGLE.DE':.03,'EUNA.DE':.032,'IBCI.DE':.03,'DBXG.DE':.036,'XEON.DE':.02,'4GLD.DE':.04,'EXXY.DE':.035,'SAT':.07}
RF=.02
stocks=pos[pos.category.isin(['STOCK','ETC'])&(pos.ticker!='4GLD.DE')]
sw=(stocks.set_index('ticker').weight/stocks.weight.sum())
R['SAT']=(R[sw.index]*sw).sum(axis=1)
# current weights
_ns={}; exec(open('load.py').read(),_ns)
LIQ=float(_ns['cash'][_ns['cash'].acct=='LIQUID'].Amount.astype(float).sum())   # conto liquidità separato
TOTI=risk['equity']-LIQ
wcur={t:v/TOTI for t,v in pos.set_index('ticker').value.items()}; wcur['XEON.DE']=(risk['cash']-LIQ)/TOTI
cur_series=sum(R[k]*v for k,v in wcur.items())
U=['VWCE.DE','SPPW.DE','EUNL.DE','XDWD.DE','SXR8.DE','SXRV.DE','QDVE.DE','XAIX.DE','SXRT.DE','VGWD.DE','VDIV.DE','IS3S.DE']+CAND+['SAT']
U=list(dict.fromkeys(U))
# weekly
Wk=(1+R).resample('W-FRI').prod()-1
Wk=Wk[Wk.index<=END]
lw=LedoitWolf().fit(Wk[U].values); S=lw.covariance_*52
mu=np.array([MU[u] for u in U]); n=len(U)
# current in U-space (stocks→SAT)
w0=np.array([wcur.get(u,0) for u in U]); w0[U.index('SAT')]=stocks.value.sum()/TOTI
print('w0 sum',w0.sum())
vol=lambda w: float(np.sqrt(w@S@w))
mu0=float(w0@mu); v0=vol(w0); print('current mu',mu0,'vol',v0)
ub=np.array([0.10 if u in ('SAT','XEON.DE') else 0.20 for u in U]); bnds=list(zip([0]*n,ub))
eqmask=np.array([CLS[u].startswith('Azioni') or u=='TRET.DE' for u in U],float)
cons_sum={'type':'eq','fun':lambda w: w.sum()-1}
x0=np.ones(n)/n
def cvar_lp(X,mut,a=.95):
    T=len(X)
    c=np.r_[np.zeros(n),1,np.ones(T)/((1-a)*T)]
    A_ub=np.c_[-X,-np.ones(T),-np.eye(T)]; b_ub=np.zeros(T)
    A_ub=np.r_[A_ub,[np.r_[-mu,0,np.zeros(T)]]]; b_ub=np.r_[b_ub,-mut]
    lp=linprog(c,A_ub=A_ub,b_ub=b_ub,A_eq=[np.r_[np.ones(n),0,np.zeros(T)]],b_eq=[1],bounds=bnds+[(None,None)]+[(0,None)]*T,method='highs')
    w=np.clip(lp.x[:n],0,None); return w/w.sum()
def resampled(X,mut,k=60,seed=7):
    rg=np.random.default_rng(seed); acc=np.zeros(n)
    for _ in range(k):
        acc+=cvar_lp(X[rg.integers(0,len(X),len(X))],mut)
    w=acc/k; w[w<.01]=0; return w/w.sum()
def growth(Sx):
    vx=lambda w: float(np.sqrt(w@Sx@w))
    r=minimize(lambda w: -(w@mu),x0,bounds=bnds,constraints=[cons_sum,{'type':'ineq','fun':lambda w: V_REF-vx(w)}],method='SLSQP',options={'maxiter':500})
    w=np.clip(r.x,0,None); w[w<.01]=0; return w/w.sum()
X=Wk[U].values
MU_REF=0.061563; V_REF=0.145008  # obiettivi fissati al 27/10/2026
wD=resampled(X,MU_REF); wO=resampled(X,MU_REF+0.007); wG=growth(S)
IG=U.index('4GLD.DE')
def with_gold(fn,*a):
    global bnds
    old=bnds; b=list(bnds); b[IG]=(0.10,0.20); bnds=b
    try: return fn(*a)
    finally: bnds=old
wR=with_gold(resampled,X,float(wO@mu))
# out-of-sample: estimate on 2021-2023, test 2024+
cut=pd.Timestamp('2023-12-31'); Xin=Wk[U][Wk.index<=cut].values
Sin=LedoitWolf().fit(Xin).covariance_*52
OOSW={'attuale':w0,'difensivo':resampled(Xin,MU_REF,30),'ottimale':resampled(Xin,MU_REF+0.007,30),'crescita':growth(Sin)}
OOSW['oro']=with_gold(resampled,Xin,MU_REF+0.007,30)
PORT={'attuale':w0,'difensivo':wD,'ottimale':wO,'oro':wR,'crescita':wG}
LBL={'attuale':'Attuale','difensivo':'Difensivo','ottimale':'Ottimale','oro':'Ottimale + Oro','crescita':'Crescita'}
DESC={'attuale':'Il portafoglio di oggi.','difensivo':'Minimo CVaR settimanale 95% a parità di rendimento atteso attuale.','ottimale':'Minimo CVaR settimanale 95% con rendimento atteso +0,7 punti sopra l’attuale.','crescita':'Massimo rendimento atteso a parità di volatilità attuale.','oro':'Stesso rendimento atteso dell’Ottimale, con almeno 10% di oro fisico (Xetra-Gold), minimo CVaR.'}
for k,w in PORT.items(): print(k, {U[i]:round(w[i],3) for i in range(n) if w[i]>.004}, 'mu',round(w@mu,4),'vol',round(vol(w),4))
# backtest daily, monthly rebal
def bt(w):
    wd=dict(zip(U,w)); idx=[1.0]; cur=None; vals=[]
    rets=R[U].values; out=np.empty(len(R)); hold=np.array(w,float)
    months=R.index.to_period('M')
    V=1.0
    for i in range(len(R)):
        if i==0 or months[i]!=months[i-1]: hold=np.array(w,float)*V
        hold=hold*(1+rets[i]); V=hold.sum(); out[i]=V
    return pd.Series(out,index=R.index)
BT={k:bt(w) for k,w in PORT.items()}
BT['vwce']=(1+B).cumprod()
def mdd(s): return float((s/s.cummax()-1).min())
STRESS=[('s2022','2022-01-03','2022-10-12'),('s2024','2024-07-10','2024-08-05'),('s2025','2025-02-19','2025-04-08')]
yrs=(R.index[-1]-R.index[0]).days/365.25
rows=[]
for k,w in PORT.items():
    s=BT[k]; wr=Wk[U].values@w; q=np.percentile(wr,5)
    C=np.corrcoef(Wk[U].values.T); idx=[i for i in range(n) if w[i]>.004]
    ww=w[idx]; Cs=C[np.ix_(idx,idx)]
    avgc=float((ww@Cs@ww - (ww**2).sum())/(1-(ww**2).sum()))
    sd=np.sqrt(np.diag(S)); dr=float(w@sd/vol(w))
    rc=w*(S@w)/vol(w)**2; effn=float(1/(rc**2).sum())
    dret=s.pct_change().dropna()
    row=dict(id=k,name=LBL[k],description=DESC[k],mu=round(float(w@mu),4),vol=round(vol(w),4),sharpe=round(float((w@mu-RF)/vol(w)),2),
      cagr_bt=round(float(s.iloc[-1]**(1/yrs)-1),4),maxdd_bt=round(mdd(s),4),cvar95w=round(float(-wr[wr<=q].mean()),4),
      corr_vwce=round(float(np.corrcoef(wr,Wk['VWCE.DE'])[0,1]),2),avg_corr=round(avgc,2),div_ratio=round(dr,2),eff_n=round(effn,1),
      vol_bt=round(float(dret.std()*np.sqrt(252)),4),skew=round(float(dret.skew()),2),kurt=round(float(dret.kurt()),2),
      calmar=round(float((s.iloc[-1]**(1/yrs)-1)/-mdd(s)),2))
    so=bt(OOSW[k]); so=so[so.index>cut]; so=so/so.iloc[0]; yo=(so.index[-1]-so.index[0]).days/365.25
    row.update(oos_cagr=round(float(so.iloc[-1]**(1/yo)-1),4),oos_maxdd=round(mdd(so),4),oos_vol=round(float(so.pct_change().std()*np.sqrt(252)),4))
    for sid,a_,b_ in STRESS: row[sid]=round(float(s.asof(pd.Timestamp(b_))/s.asof(pd.Timestamp(a_))-1),4)
    eqs=sum(w[i] for i in range(n) if eqmask[i]); bs=sum(w[i] for i in range(n) if CLS[U[i]] in('Obbligazioni','Liquidità')); gs=sum(w[i] for i in range(n) if CLS[U[i]] in ('Oro','Materie prime'))
    row.update(equity_share=round(eqs,4),bond_share=round(bs,4),real_share=round(gs,4))
    rows.append(row)
bv=BT['vwce']; br=Wk['VWCE.DE']
rows.append(dict(id='vwce',name='VWCE (benchmark)',description='100% FTSE All-World.',mu=.065,vol=round(float(np.sqrt(S[U.index('VWCE.DE'),U.index('VWCE.DE')])),4),sharpe=round((.065-RF)/float(np.sqrt(S[0,0])),2),cagr_bt=round(float(bv.iloc[-1]**(1/yrs)-1),4),maxdd_bt=round(mdd(bv),4),cvar95w=round(float(-br[br<=np.percentile(br,5)].mean()),4),corr_vwce=1.0,avg_corr=None,div_ratio=1.0,eff_n=1.0,vol_bt=round(float(B.std()*np.sqrt(252)),4),skew=round(float(B.skew()),2),kurt=round(float(B.kurt()),2),calmar=round(float((bv.iloc[-1]**(1/yrs)-1)/-mdd(bv)),2),oos_cagr=round(float((bv[bv.index>cut].iloc[-1]/bv[bv.index>cut].iloc[0])**(1/((bv.index[-1]-cut).days/365.25))-1),4),oos_maxdd=round(mdd(bv[bv.index>cut]),4),oos_vol=round(float(B[B.index>cut].std()*np.sqrt(252)),4),**{sid:round(float(bv.asof(pd.Timestamp(b_))/bv.asof(pd.Timestamp(a_))-1),4) for sid,a_,b_ in STRESS},equity_share=1.0,bond_share=0.0,real_share=0.0))
print(pd.DataFrame(rows).drop(columns=['description']).to_string())
# weights & trades
TOT=TOTI
nm=dict(zip(pos.ticker,pos.name)); nm.update(NAMES); nm['XEON.DE']='Liquidità / XEON (€STR)'; nm['SAT']='Azioni singole e ETC (satellite)'
wrows=[]
for k,w in PORT.items():
    for i,u in enumerate(U):
        if u=='SAT':
            for t,s_ in sw.items():
                cw=wcur.get(t,0); tw=w[i]*s_
                if cw>0 or tw>.0005: wrows.append(dict(portfolio=k,ticker=t,name=nm.get(t,t),cls='Azioni singole' if t!='ISLN.UK' else 'Argento (ETC)',current=round(cw,4),target=round(tw,4),current_eur=round(cw*TOT,2),target_eur=round(tw*TOT,2),delta_eur=round((tw-cw)*TOT,2)))
            continue
        cw=wcur.get(u,0); tw=float(w[i])
        if cw>0 or tw>.004:
            if tw<=.004: tw=0.0
            wrows.append(dict(portfolio=k,ticker=u,name=nm.get(u,u),cls=CLS[u],current=round(cw,4),target=round(tw,4),current_eur=round(cw*TOT,2),target_eur=round(tw*TOT,2),delta_eur=round((tw-cw)*TOT,2)))
# frontier
fr=[]
mus=np.linspace(min(mu)+.002,max(mu),26)
xs=x0
for m in mus:
    r=minimize(lambda w: w@S@w,xs,bounds=bnds,constraints=[cons_sum,{'type':'eq','fun':lambda w,m=m: w@mu-m}],method='SLSQP')
    if r.success: fr.append(dict(kind='frontiera',label='',vol=round(vol(r.x),4),mu=round(float(r.x@mu),4))); xs=r.x
for i,u in enumerate(U): fr.append(dict(kind='strumento',label=u,vol=round(float(np.sqrt(S[i,i])),4),mu=MU[u]))
for k,w in PORT.items(): fr.append(dict(kind='portafoglio',label=LBL[k],vol=round(vol(w),4),mu=round(float(w@mu),4)))
# screener: candidate effects
cw_vec=w0
scr=[]
for u in U:
    if u=='SAT': continue
    i=U.index(u); w1=w0*0.9; w1[i]+=0.1
    wr=Wk[U].values@w0
    s1=bt(w1)
    scr.append(dict(ticker=u,name=nm.get(u,u),cls=CLS[u],held=bool(wcur.get(u,0)>0),mu=MU[u],vol=round(float(np.sqrt(S[i,i])),4),
      cagr_5y=round(float((1+R[u]).prod()**(1/yrs)-1),4),maxdd_5y=round(mdd((1+R[u]).cumprod()),4),
      corr_port=round(float(np.corrcoef(Wk[u],wr)[0,1]),2),beta_vwce=round(float(np.cov(Wk[u],br)[0,1]/br.var()),2),
      d_vol=round(vol(w1)-v0,4),d_mu=round(float(w1@mu-mu0),4),d_sharpe=round(float((w1@mu-RF)/vol(w1)-(mu0-RF)/v0),3),d_maxdd=round(mdd(s1)-mdd(BT['attuale']),4)))
scr.sort(key=lambda r:-r['d_sharpe'])
print(pd.DataFrame(scr)[['ticker','corr_port','d_vol','d_mu','d_sharpe','d_maxdd','cagr_5y','maxdd_5y']].to_string())
# backtest weekly sampled
bw=pd.DataFrame(BT).resample('W-FRI').last(); bw=bw[bw.index<=END]
ddw=pd.DataFrame({k:(v/v.cummax()-1) for k,v in BT.items()}).resample('W-FRI').min(); ddw=ddw[ddw.index<=END]
btrows=[dict(day=d.strftime('%Y-%m-%d'),**{k:round(float(bw.loc[d,k])*100,2) for k in bw},**{'dd_'+k:round(float(ddw.loc[d,k]),4) for k in ddw}) for d in bw.index]
# rolling current portfolio (actual holdings)
cs=cur_series
rv=cs.rolling(63).std()*np.sqrt(252); rc=cs.rolling(63).corr(B)
rb=B.rolling(63).std()*np.sqrt(252)
roll=pd.DataFrame({'vol':rv,'corr':rc,'vol_vwce':rb}).dropna().resample('W-FRI').last()
rollrows=[dict(day=d.strftime('%Y-%m-%d'),vol=round(float(r.vol),4),corr=round(float(r['corr']),3),vol_vwce=round(float(r.vol_vwce),4)) for d,r in roll.iterrows() if d<=END]
# distribution of daily returns, last 2y
x=cs[cs.index>=END-pd.Timedelta(days=730)]
edges=np.linspace(-0.05,0.05,41); cnt,_=np.histogram(x.clip(-0.0499,0.0499),edges)
from scipy.stats import norm
m_,s_=x.mean(),x.std()
dist=[dict(lo=round(edges[i],4),hi=round(edges[i+1],4),n=int(cnt[i]),normal=round(float(len(x)*(norm.cdf(edges[i+1],m_,s_)-norm.cdf(edges[i],m_,s_))),2)) for i in range(40)]
for nme,o in dict(portfolios=rows,weights=wrows,frontier=fr,screener=scr,backtest=btrows,rolling=rollrows,dist=dist).items():
    json.dump(o,open(f'../data/out/{nme}.json','w'),ensure_ascii=False)
print(len(btrows),len(rollrows))
