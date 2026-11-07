import io, contextlib, json, numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    exec(open('opt.py').read())
from sklearn.covariance import LedoitWolf
add={}
for t in ['MSFT','GOOGL','STLAM.MI']:
    s=eur(t); add[t]=s.pct_change(fill_method=None).reindex(R.index).fillna(0)
wT=dict(zip(U,wR))   # Ottimale + Oro target
port=sum(R[u]*w for u,w in wT.items() if w>0)
B=R['VWCE.DE']
Wp=(1+port).resample('W-FRI').prod()-1; Wb=(1+B).resample('W-FRI').prod()-1
res=[]
mu_t=float(sum(MU[u]*w for u,w in wT.items()))
for t,r in add.items():
    Wt=(1+r).resample('W-FRI').prod()-1
    X=pd.concat([Wp,Wt,Wb],axis=1).dropna().values
    C=np.cov(X.T)*52
    vp=np.sqrt(C[0,0]); vt=np.sqrt(C[1,1])
    out=dict(ticker=t,vol=round(float(vt),4),corr_target=round(float(C[0,1]/vp/vt),3),beta_vwce=round(float(C[1,2]/C[2,2]),2),corr_portfolio_now=None)
    for a in (0.05,0.10):
        w=np.array([1-a,a]); v=np.sqrt(w@C[:2,:2]@w)
        rho=(w@C[:2,2])/(v*np.sqrt(C[2,2]))
        rho0=C[0,2]/(vp*np.sqrt(C[2,2]))
        newd=(1-a)*port+a*r; idx=(1+newd).cumprod(); idx0=(1+port).cumprod()
        out[f'd_vol_{int(a*100)}']=round(float(v-vp),4); out[f'd_rho_{int(a*100)}']=round(float(rho-rho0),3)
        out[f'd_dd_{int(a*100)}']=round(float((idx/idx.cummax()-1).min()-(idx0/idx0.cummax()-1).min()),4)
    idx=(1+r).cumprod(); out['maxdd_5y']=round(float((idx/idx.cummax()-1).min()),4)
    out['cagr_5y_eur']=round(float(idx.iloc[-1]**(252/len(r))-1),4)
    # corr with current portfolio
    cur=sum(R[k]*v for k,v in wcur.items() if k in R)
    Wc=(1+cur).resample('W-FRI').prod()-1
    out['corr_portfolio_now']=round(float(np.corrcoef(pd.concat([Wc,Wt],axis=1).dropna().values.T)[0,1]),3)
    res.append(out)
print(pd.DataFrame(res).to_string()); print('target vol',np.sqrt(np.cov(Wp)*52), 'rho',np.corrcoef(Wp,Wb)[0,1])
json.dump(res,open('../data/out/xtb_fit.json','w'))
