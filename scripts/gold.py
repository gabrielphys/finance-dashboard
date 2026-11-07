import io, contextlib, json, numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    exec(open('opt.py').read())
ig=U.index('4GLD.DE'); muO=float(wO@mu); muG=float(wG@mu)
def resampled_g(X,mut,gmin,k=60,seed=7):
    global bnds
    old=bnds; b=list(bnds); b[ig]=(gmin,0.20); bnds=b
    try: w=resampled(X,mut,k,seed)
    finally: bnds=old
    return w
res={}
for g in [0.10,0.125,0.15]:
    for tgt in [muO]:
        try: w=resampled_g(X,tgt,g,30)
        except TypeError: print(f'g={g}: rendimento {tgt:.4f} non raggiungibile con questo minimo di oro, salto'); continue
        s_=bt(w); wr=X@w; q=np.percentile(wr,5)
        res[(g,round(tgt,4))]=w
        print(f"g={g} tgt={tgt:.4f} mu={w@mu:.4f} gold={w[ig]:.3f} vol={vol(w):.4f} cvar={-wr[wr<=q].mean():.4f} mdd={mdd(s_):.4f} cagr={s_.iloc[-1]**(1/yrs)-1:.4f} corr={np.corrcoef(wr,Wk['VWCE.DE'])[0,1]:.3f}")
import pickle;pickle.dump({k:v for k,v in res.items()},open('../data/out/gold_res.pkl','wb'))
print('ottimale', wO@mu, vol(wO), mdd(BT['ottimale']))
