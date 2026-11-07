import io, contextlib, json, numpy as np
with contextlib.redirect_stdout(io.StringIO()):
    exec(open('opt.py').read())
from scipy.optimize import minimize
TOT=TOTI
# U-space holdings in EUR
h0=w0*TOT
ix={u:i for i,u in enumerate(U)}
cash=h0[ix['XEON.DE']]
wstar=wR.copy()
def solve(H=12,m=240,deploy=True):
    hh=h0.copy(); extra=0
    if deploy: hh[ix['XEON.DE']]=0; extra=cash
    K=H*m+extra; N=hh.sum()+K
    cand=[i for i in range(n) if wstar[i]>0]
    def f(v):
        full=np.zeros(n); full[cand]=v
        return (((hh+K*full)/N-wstar)**2).sum()
    v0=np.ones(len(cand))/len(cand)
    r=minimize(f,v0,bounds=[(0,1)]*len(cand),constraints=[{'type':'eq','fun':lambda v:v.sum()-1}],method='SLSQP')
    v=np.zeros(n); v[cand]=r.x
    # XTB-friendly: integer %, min 5%
    v[v<0.04]=0; v=v/v.sum(); p=np.round(v*100)
    p[np.argmax(p)]+=100-p.sum()
    return p/100
# PAC C reale (creato il 30/10/2026): pesi dagli acquisti del primo versamento
vC=np.zeros(n)
for t,w in {'IS3N.DE':.24,'ZPRX.DE':.21,'ZPRV.DE':.16,'VDIV.DE':.11,'IS3S.DE':.11,'4GLD.DE':.09,'VGWD.DE':.08}.items(): vC[ix[t]]=w
print({U[i]:vC[i] for i in range(n) if vC[i]>0})
dist=lambda h: float(np.abs(h/h.sum()-wstar).sum()/2)
print('dist now',dist(h0))
for H in [6,12,24,36]:
    hh=h0.copy(); hh=hh+vC*(H*240); print(H,dist(hh))
nm=dict(zip(pos.ticker,pos.name)); nm.update(NAMES)
# existing plans from open lots
A={'SXRV.DE':.40,'SPPW.DE':.15,'EUNL.DE':.15,'XDWD.DE':.15,'VWCE.DE':.15}
B={'VGWD.DE':.12,'IS3S.DE':.11,'VDIV.DE':.11,'VWCE.DE':.11,'SXRT.DE':.11,'SXR8.DE':.11,'QDVE.DE':.11,'XAIX.DE':.11,'SXRV.DE':.11}
_ns={}; exec(open('load.py').read(),_ns); _o=_ns['opn']
summ=_o[(_o.Type=='')&(_o.Product.str.startswith('Investment'))][['Ticker','Value']].values.tolist()
SETS={'C':set(['IS3N.DE','ZPRX.DE','ZPRV.DE','VDIV.DE','IS3S.DE','4GLD.DE','VGWD.DE']),'A':set(A),'B':set(B)}
vals={'A':{},'B':{},'C':{}}; curp=None
for t,v in summ:
    if curp is None or t in vals[curp] or t not in SETS[curp]:
        curp=next(p for p in ['C','A','B'] if t in SETS[p] and t not in vals[p] and len(vals[p])<len(SETS[p]))
    vals[curp][t]=float(v)*float(P[t].asof(END)/P[t].asof(EXP))   # valore export portato a END
print(vals)
valA,valB,valC=vals['A'],vals['B'],vals['C']
rows=[]
WC={U[i]:float(vC[i]) for i in range(n) if vC[i]>0}
for plan,lab,W,V,status in [('A','PAC A · World + Nasdaq',A,valA,'pausa'),('B','PAC B · Multi-fattore',B,valB,'pausa'),('C','PAC C · Ribilanciamento + Oro',WC,valC,'attivo')]:
    for t,w in W.items(): rows.append(dict(plan=plan,plan_name=lab,status=status,ticker=t,name=nm.get(t,t),cls=CLS[t],weight=w,value=V[t],target_w=round(float(wstar[ix[t]]),4)))
json.dump(rows,open('../data/out/xtb_pacs.json','w'),ensure_ascii=False)
# model: per U instrument mu, current eur, target weight; cov long
model=[dict(ticker=u,name=('Azioni singole (blocco)' if u=='SAT' else nm.get(u,u)),cls=CLS.get(u,'Liquidità'),mu=MU[u],current_eur=round(float(h0[i]),2),target_w=round(float(wstar[i]),4)) for i,u in enumerate(U)]
json.dump(model,open('../data/out/xtb_model.json','w'),ensure_ascii=False)
cov=[dict(a=U[i],b=U[j],cov=round(float(S[i,j]),7)) for i in range(n) for j in range(n)]
json.dump(cov,open('../data/out/xtb_cov.json','w'))
print(len(cov), sum(r['current_eur'] for r in model))
