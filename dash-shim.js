// Sostituisce il runtime `dash` di Cowork: carica i JSON da data/out e li serve alla dashboard.
(() => {
  const F = {allocation:'xtb_allocation_u30', backtest:'xtb_backtest_u30', corr:'xtb_corr_u30', cov:'xtb_cov_u30',
    dist:'xtb_dist_u30', equity:'xtb_equity_u30', flows:'xtb_flows_u30', frontier:'xtb_frontier_u30',
    liquidity:'xtb_liquidity_v2', model:'xtb_model_u30', pacs:'xtb_pacs_u30', portfolios:'xtb_portfolios_u30',
    positions:'xtb_positions_u30', realized:'xtb_realized_u30', risk:'xtb_risk_u30', rolling:'xtb_rolling_u30',
    scenarios:'xtb_scenarios_v2', screener:'xtb_screener_u30', weights:'xtb_weights_u30'};
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
  Promise.all(Object.entries(F).map(([id, f]) =>
    fetch(`data/out/${f}.json`).then(r => r.json()).then(d => { S[id] = {status:'ok', data:d}; })
      .catch(() => { S[id] = {status:'error', data:[]}; })
  )).then(() => { runCalcs(); fire(); });
})();
