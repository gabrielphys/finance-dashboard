import json, urllib.request, time, sys, os
os.makedirs('../data/prices5',exist_ok=True)
# simboli Yahoo usati da opt.py (HOLD + CAND + cambi) e fit.py
DEFAULT=['EURUSD=X','EURGBP=X','SXRV.DE','VWCE.DE','SPPW.DE','EUNL.DE','XDWD.DE','TPRO.MI','VGWD.DE','IS3S.DE','VDIV.DE','SXRT.DE','SXR8.DE','QDVE.DE','XAIX.DE','SPCX','ISP.MI','TSLA','ISLN.L','ATS.VI','STMMI.MI','RACE.MI','PTX.DE','MH6.F',
 '4GLD.DE','XGLE.DE','EUNA.DE','IBCI.DE','XEON.DE','IQQ0.DE','IS3N.DE','ZPRV.DE','ZPRX.DE','IS3Q.DE','EXXY.DE','DBXG.DE','XDEM.DE','TRET.DE','MSFT','GOOGL','STLAM.MI']
def get(sym):
    u=f'https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1=1609459200&period2={int(time.time())}&interval=1d'
    return json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=20))['chart']['result'][0]
for s in sys.argv[1:] or DEFAULT:
    out=s.replace('/','_')
    try:
        j=get(s); ts=j['timestamp']; q=j['indicators']
        c=(q.get('adjclose') or [{}])[0].get('adjclose') or q['quote'][0]['close']
        json.dump({'sym':s,'cur':j['meta']['currency'],'name':j['meta'].get('longName') or j['meta'].get('shortName'),'ts':ts,'c':c},open(f'../data/prices5/{out}.json','w'))
        print(s,len(ts),end='; ')
    except Exception as e: print(s,'ERR',str(e)[:50])
    time.sleep(0.2)
