import json, numpy as np, pandas as pd, io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    exec(open('opt.py').read())
P=(1+R).cumprod()                      # EUR total-return index per instrument (daily)
M=P.resample('ME').last()
wOro=dict(zip(U,wR)); wOro={k:v for k,v in wOro.items() if v>0}
A={'SXRV.DE':.40,'SPPW.DE':.15,'EUNL.DE':.15,'XDWD.DE':.15,'VWCE.DE':.15}
nas=P['SXRV.DE']; dd_nas=(nas/nas.cummax()-1).resample('ME').last()
rn=0.02*0.74/12
def run(trigger=-0.20, extra=200, dest='A', base=240, liq_in=80, liq0=1000, reserve=500, cooldown=0):
    units={}; L=liq0; hist=[]; inv=0; lastbuy=-99; buys=[]
    def buy(w,amt,dt):
        for t,x in w.items(): units[t]=units.get(t,0)+amt*x/M.loc[dt,t]
    for i,dt in enumerate(M.index):
        buy(wOro,base,dt); inv+=base
        L=L*(1+rn)+liq_in
        if dest and dd_nas.loc[dt]<=trigger and L-extra>=reserve and i-lastbuy>cooldown:
            buy(A if dest=='A' else wOro,extra,dt); L-=extra; inv+=extra; lastbuy=i; buys.append(dt.strftime('%Y-%m'))
        V=sum(u*M.loc[dt,t] for t,u in units.items())
        tech=units.get('SXRV.DE',0)*M.loc[dt,'SXRV.DE']/V
        hist.append((dt,V,L,inv,tech))
    h=pd.DataFrame(hist,columns=['d','V','L','inv','tech']).set_index('d')
    tot=h.V+h.L
    # TWR-ish monthly return of investments excluding flows
    return h,buys
res={}
for name,kw in {'Base (solo PAC C + liquidità)':dict(dest=None),
                'Dip → PAC A (Nasdaq −20%)':dict(dest='A'),
                'Dip → PAC C (stesso trigger)':dict(dest='C'),
                'Dip → PAC A (Nasdaq −15%)':dict(dest='A',trigger=-0.15),
                'Stesso importo in PAC C ogni mese (no timing)':dict(dest=None,base=240)}.items():
    h,b=run(**kw); res[name]=(h,b)
# no-timing equivalent: spread total extra evenly
hA,bA=res['Dip → PAC A (Nasdaq −20%)']
nb=len(bA); ext=nb*200/len(M)
h,_=run(dest=None,base=240+ext,liq_in=80-ext); res['Stesso importo in PAC C ogni mese (no timing)']=(h,[])
for k,(h,b) in res.items():
    f=h.iloc[-1]; mret=(h.V.diff()-h.inv.diff()).iloc[1:]/h.V.shift().iloc[1:]
    # money-weighted: final investments / invested
    print(f"{k:48s} buys={len(b):2d} inv={f.inv:7.0f} V={f.V:7.0f} gain={f.V-f.inv:6.0f} mult={f.V/f.inv:.3f} L={f.L:6.0f} tot={f.V+f.L:7.0f} tech={f.tech:.2f} maxDDvol={( (h.V/h.inv)/(h.V/h.inv).cummax()-1).min():.3f}")
print(bA)
print(dd_nas[dd_nas<=-0.15].index.strftime('%Y-%m').tolist())
