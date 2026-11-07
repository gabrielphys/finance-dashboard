// Sostituisce il runtime `dash` di Cowork: carica i JSON da data/out e li serve alla dashboard.
(() => {
  const F = {allocation:'allocation', backtest:'backtest', corr:'corr', cov:'xtb_cov', dist:'dist', equity:'equity',
    flows:'flows', frontier:'frontier', liquidity:'xtb_liquidity_v2', model:'xtb_model', pacs:'xtb_pacs',
    portfolios:'portfolios', positions:'positions', realized:'realized', risk:'risk', rolling:'rolling',
    scenarios:'xtb_scenarios_v2', screener:'screener', weights:'weights'};   // dati rigenerati da GitHub Actions ogni 15 min
  const S = {}, calcs = [], cbs = [];
  let params = {};
  const fire = () => cbs.forEach(f => f());
  const runCalcs = () => calcs.forEach(c => { if (c.inputs.every(i => S[i] && S[i].status === 'ok')) S[c.id] = {status:'ok', data:c.fn(...c.inputs.map(i => S[i].data))}; });
  window.dash = {
    calc: (id, o) => calcs.push({id, inputs:o.inputs, fn:o.fn}),
    data: id => S[id] || {status:'loading', data:[]},
    onData: f => { cbs.push(f); f(); },
    params: () => params,
    setParams: o => { params = {...params, ...o}; fire(); },
    setLink: () => {},
  };
  const load = () => Promise.all(Object.entries(F).map(([id, f]) =>
    fetch(`data/out/${f}.json`, {cache:'no-store'}).then(r => r.json()).then(d => { S[id] = {status:'ok', data:d}; })
      .catch(() => { if (!S[id]) S[id] = {status:'error', data:[]}; })
  )).then(() => { runCalcs(); fire(); return fetch('data/out/meta.json', {cache:'no-store'}).then(r => r.json()).then(m => {
    const el = document.getElementById('asof'); if (el) el.title = 'Aggiornato ' + new Date(m.updated).toLocaleString('it-IT');
    let u = document.getElementById('upd'); if (!u && el) { u = document.createElement('span'); u.id = 'upd'; el.parentNode.append(' · agg. ', u); }
    if (u) u.textContent = new Date(m.updated).toLocaleTimeString('it-IT', {hour:'2-digit', minute:'2-digit'});
  }).catch(() => {}); });
  load(); setInterval(load, 15 * 60 * 1000);
})();
