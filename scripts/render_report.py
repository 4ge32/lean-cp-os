#!/usr/bin/env python3
import html,json,pathlib,sys
out=pathlib.Path(sys.argv[1]);r=json.loads((out/'report.json').read_text());esc=lambda x:html.escape(str(x))
t=json.loads((out/'trace.json').read_text()) if (out/'trace.json').exists() else {'requirements':[],'gaps':['Trace not run']}
a=json.loads((out/'axioms.json').read_text()) if (out/'axioms.json').exists() else {'theorems':[]}
def link(path,label=None):return '<a href="'+esc(path)+'">'+esc(label or path)+'</a>'
css='body{font:16px system-ui;margin:40px auto;padding:0 20px;max-width:1250px;background:#101820;color:#e7edf4}a{color:#80cfff}h1,h2{color:#fff}table{border-collapse:collapse;width:100%;margin:20px 0}td,th{border:1px solid #415063;padding:9px;text-align:left;vertical-align:top;font-size:14px}code{overflow-wrap:anywhere}small{color:#b9c9d8}.passed,.checked{color:#8ae8b0}.failed{color:#ff9c9c}.not_run,.unproved{color:#ffd483}article{border-top:1px solid #506070;padding:10px 0}.banner{background:#304052;padding:16px}details{margin:12px 0}li{margin:8px 0}'
body=f'<h1>Lean CP OS — commit evidence</h1><p class="banner">Gate result: <b>{esc(r.get("overall","not_run"))}</b> · Coverage: <b>INCOMPLETE</b> · No BCC1 / SC1 / AUTOSAR conformance claim</p><p>Commit <code>{esc(r["sha"])}</code><br>Tree <code>{esc(r["tree_sha"])}</code><br>Run {esc(r["run_id"])} / attempt {esc(r["attempt"])}<br>Exact commit: {esc(r["exact_commit"])} · Source unchanged: {esc(r.get("source_unchanged",False))}</p>'
if r.get('repository') and r['run_id'].isdigit():body+=link(f'https://github.com/{r["repository"]}/actions/runs/{r["run_id"]}','GitHub Actions run')
body+='<p>'+ ' · '.join(link(x) for x in ['report.json','trace.json','axioms.json','runtime.json','SHA256SUMS','test-results/tests.json','test-results/task-control.json','qemu/qemu.json','qemu/uart.log'] if (out/x).exists() or x=='SHA256SUMS')+'</p><h2>Verification gates</h2><table><tr><th>Gate</th><th>State</th><th>Evidence</th></tr>'
for s in r['stages']:body+=f'<tr><td>{esc(s["name"])}</td><td class="{esc(s["status"])}">{esc(s["status"])}</td><td>{link(s["log"]) if "log" in s else esc(s.get("reason","snapshot check"))}</td></tr>'
body+='</table><h2>Requirements → source → proof → generated C → tests</h2><p>Implementation, proof, and test states are independent. “Checked” applies only to the linked theorem statements under their assumptions.</p>'
for q in t['requirements']:
    body+=f'<article id="{esc(q["id"])}"><h3>{esc(q["id"])} — {esc(q["title"])}</h3><p>Scope: {esc(q["scope"])} · implementation: {esc(q["implementation"])} · proof: {esc(q["proof"])} · test: {esc(q["test"])}</p>'
    body+='<p>Sources: '+esc('; '.join(x['document']+' §'+x['section']+(' ['+', '.join(x['requirement_ids'])+']' if x['requirement_ids'] else '') for x in q['sources']))+'</p>'
    body+='<details><summary>Definitions, assumptions, symbols, boundaries and tests</summary><pre>'+esc(json.dumps({k:q[k] for k in ['definitions','theorems','assumptions','generated_symbols','boundaries','tests']},indent=2))+'</pre></details>'
    if q.get('limitation'):body+='<p>'+esc(q['limitation'])+'</p>'
    body+='</article>'
body+='<h2>Axiom dependencies</h2><table><tr><th>Theorem</th><th>Axioms</th></tr>'
for x in a['theorems']:body+='<tr><td>'+esc(x['theorem'])+'</td><td>'+esc(', '.join(x['axioms']) or 'none')+'</td></tr>'
body+='</table><h2>Open gaps</h2><ul>'+''.join('<li>'+esc(x)+'</li>' for x in t['gaps'])+'</ul><h2>Proof / runtime limits</h2><ul>'+''.join('<li>'+esc(x)+'</li>' for x in r['limitations'])+'</ul>'
(out/'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Lean CP OS evidence</title><style>'+css+'</style><body>'+body+'</body></html>')
