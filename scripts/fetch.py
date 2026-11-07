import json, urllib.request, time, os, sys
exec(open('load.py').read())
tick=sorted((set(closed[closed.Category!='CFD'].Ticker)|set(opn[opn.Type==''].Ticker)))
def ymap(t):
    if t in ('ATS.DE','STM.IT'): return {'ATS.DE':['ATS.VI'],'STM.IT':['STMMI.MI']}[t]   # simboli Yahoo diversi
    b,s=t.rsplit('.',1)
    return {'US':[b],'DE':[t,b+'.F'],'IT':[b+'.MI'],'FR':[b+'.PA'],'UK':[b+'.L']}[s]
os.makedirs('../data/prices',exist_ok=True)
def get(sym):
    u=f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1=1727740800&period2={int(time.time())}&interval=1d'
    r=urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'})
    return json.load(urllib.request.urlopen(r,timeout=20))
res={}
for t in tick+['EURUSD=X','EURGBP=X','URTH']:
    for sym in (ymap(t) if '.' in t and not t.endswith('=X') else [t]):
        try:
            j=get(sym)['chart']['result'][0]
            ts=j['timestamp']; c=j['indicators']['quote'][0]['close']; cur=j['meta']['currency']
            json.dump({'sym':sym,'cur':cur,'ts':ts,'c':c},open(f'../data/prices/{t}.json','w'))
            res[t]=(sym,cur,len(ts)); break
        except Exception as e: res[t]=('ERR',str(e)[:60])
        time.sleep(0.3)
for k,v in res.items(): print(k,v)
