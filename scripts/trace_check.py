#!/usr/bin/env python3
import json,pathlib,re,sys
from lean_declarations import declarations
out=pathlib.Path(sys.argv[1]); errors=[]; gaps=[]
def read(p):return json.loads(pathlib.Path(p).read_text())
r=read('trace/requirements.json'); sources={s['id']:s for s in read('trace/sources.json')['sources']}
tests={t['id']:t for t in read('trace/tests.json')['tests']}
assumptions={a['id'] for a in r['assumptions']}
c='\n'.join(p.read_text() for p in pathlib.Path('build').glob('*.c'))
inventory=declarations()
decls={row['name'] for row in inventory}
all_thms={row['name'] for row in inventory if row['kind']=='theorem'}
seen=set(); used=set(); reverse={}; rows=[]
audit=read(out/'axioms.json') if (out/'axioms.json').exists() else {'theorems':[]}
proved={x['theorem'] for x in audit['theorems'] if x['status']=='checked'}
testpath=out/'test-results/tests.json'
executed={t['id']:t['status'] for t in read(testpath)['tests']} if testpath.exists() else {}
taskpath=out/'test-results/task-control.json'
if taskpath.exists():
    task=read(taskpath)
    executed[task['id']]=task['status']
    if isinstance(task.get('scalar'),dict):
        executed[task['scalar']['id']]=task['scalar']['status']
qemupath=out/'qemu/qemu.json'
if qemupath.exists():
    qemu=read(qemupath)
    executed[qemu['id']]=qemu['status']
if (out/'control-flow.log').exists():
    executed['T-CONTROL']='passed' if 'PASS T-CONTROL:' in (out/'control-flow.log').read_text() else 'failed'
if (out/'evidence-selftests.log').exists():
    executed['T-EVIDENCE']='passed' if 'PASS T-EVIDENCE:' in (out/'evidence-selftests.log').read_text() else 'failed'
for q in r['requirements']:
    ident=q['id']
    if q['implementation'] not in ['implemented','partial','unimplemented','out_of_scope']:errors.append('Invalid implementation status '+ident)
    if q['proof'] not in ['unproved','checked','partial','not_applicable']:errors.append('Invalid proof status '+ident)
    if q['test'] not in ['not_run','passed','failed','partial','out_of_scope']:errors.append('Invalid test status '+ident)
    if ident in seen:errors.append('duplicate '+ident)
    seen.add(ident)
    for a in q['assumptions']:
        if a not in assumptions:errors.append(f'{ident}: unknown assumption {a}')
    for s in q['sources']:
        if s['document'] not in sources:errors.append(f'{ident}: unknown source')
        elif sources[s['document']]['sha256'] is None and sources[s['document']]['kind']!='project-decision':
            gaps.append(f'{ident}: source PDF hash unavailable: '+s['document'])
    for d in q['definitions']+q['theorems']:
        if d not in decls:errors.append(f'{ident}: missing declaration {d}')
    used.update(q['theorems'])
    for t in q['tests']:
        if t not in tests:errors.append(f'{ident}: missing test {t}')
    for f in q['files']+q['boundaries']:
        if not pathlib.Path(f).is_file():errors.append(f'{ident}: missing file {f}')
    for sym in q['generated_symbols']:
        if not re.search(r'\b'+re.escape(sym)+r'\s*[;(]',c):errors.append(f'{ident}: missing generated symbol {sym}')
    row=dict(q)
    row['proof']='checked' if q['theorems'] and all(t in proved for t in q['theorems']) else 'unproved'
    statuses=[executed.get(t,'not_run') for t in q['tests']]
    row['test']=('failed' if 'failed' in statuses else 'not_run' if not statuses or 'not_run' in statuses else 'passed')
    if q['scope']=='deferred':gaps.append(f'{ident}: deferred/unimplemented/unproved/not_run')
    elif row['proof']!='checked':gaps.append(f'{ident}: no checked proof for this boundary')
    if row['test']!='passed':gaps.append(f'{ident}: tests {row["test"]}')
    # Symmetric indices are generated from the very same edges, not hand duplicated.
    keys=q['assumptions']+[s['document']+':'+rid for s in q['sources'] for rid in s['requirement_ids']]+q['definitions']+q['theorems']+q['generated_symbols']+q['tests']+q['files']+q['boundaries']+[s['document']+':'+s['section'] for s in q['sources']]
    for key in keys:reverse.setdefault(key,[]).append(ident)
    rows.append(row)
for t in all_thms-used:errors.append('untraced theorem '+t)
identity=read(out/'report.json') if (out/'report.json').exists() else {}
result=dict(evidence_identity={k:identity.get(k) for k in ['sha','tree_sha','run_id','attempt','exact_commit']},generation={'model':'generate-model.log','bridge':'generate-bridge.log','task_scalar':'generate-task-scalar.log','compiler_flags':'compile-model.log / compile-bridge.log / compile-task-scalar.log; -O2 -fstack-usage','conditions_file':'report.json','c_assembly_boundary':'QEMU AArch64 call-boundary contexts; qemu/qemu.json records commands and scenarios; no formal assembly refinement'},structural_status='passed' if not errors else 'failed',coverage_status='incomplete' if gaps else 'complete',errors=errors,gaps=sorted(set(gaps)),requirements=rows,reverse={k:sorted(set(v)) for k,v in reverse.items()})
(out/'trace.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(structural_status=result['structural_status'],coverage_status=result['coverage_status'],errors=errors,gaps=result['gaps']),indent=2))
sys.exit(bool(errors))
