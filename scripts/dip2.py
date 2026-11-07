import io, contextlib, json, numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    exec(open('dip.py').read().split("res={}")[0])
rows=[]; series={}
specs=[('base','Base: PAC C 240 € + liquidità 80 €',dict(dest=None)),
       ('dipA20','Ricariche PAC A, Nasdaq −20%',dict(dest='A')),
       ('dipC20','Ricariche PAC C, stessa soglia',dict(dest='C')),
       ('dipA15','Ricariche PAC A, Nasdaq −15%',dict(dest='A',trigger=-0.15))]
for k,lab,kw in specs:
    h,b=run(**kw); f=h.iloc[-1]
    rows.append(dict(id=k,name=lab,buys=len(b),invested=round(f.inv,0),value=round(f.V,0),liquidity=round(f.L,0),total=round(f.V+f.L,0),gain=round(f.V-f.inv,0),tech=round(f.tech,4),buy_months=', '.join(b)))
    series[k]=(h.V+h.L)
hA,bA=run(dest='A'); ext=len(bA)*200/len(M)
h,_=run(dest=None,base=240+ext,liq_in=80-ext); f=h.iloc[-1]
rows.insert(1,dict(id='notiming',name='Stessi soldi extra nel PAC C a rate fisse',buys=0,invested=round(f.inv,0),value=round(f.V,0),liquidity=round(f.L,0),total=round(f.V+f.L,0),gain=round(f.V-f.inv,0),tech=0.0,buy_months=''))
base=rows[0]['total']
for r in rows: r['delta_total']=round(r['total']-base,0)
ser=[dict(month=d.strftime('%Y-%m'),nasdaq_dd=round(float(dd_nas.loc[d]),4),**{k:round(float(v.loc[d]),0) for k,v in series.items()},buyA=d.strftime('%Y-%m') in bA) for d in M.index]
json.dump(rows,open('../data/out/xtb_dip_summary.json','w'),ensure_ascii=False); json.dump(ser,open('../data/out/xtb_dip_series.json','w'))
print(pd.DataFrame(rows).drop(columns=['buy_months']).to_string()); print(len(ser), ser[-1])
