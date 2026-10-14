#!/usr/bin/env python3
"""Run all gates; retain failure/not_run, immutable SHA and input/output hashes."""
import argparse,datetime,hashlib,json,os,pathlib,platform,shutil,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--allow-dirty',action='store_true');a=p.parse_args()
root=pathlib.Path.cwd();out=pathlib.Path(a.out).resolve();out.mkdir(parents=True,exist_ok=True)
def digest(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def git(*args):return subprocess.check_output(['git',*args],text=True).strip()
def source_manifest():
    return {p:digest(p) for p in git('ls-files').splitlines() if pathlib.Path(p).is_file()}
def dirty():return git('status','--porcelain','--untracked-files=all')
sha=git('rev-parse','HEAD');tree=git('rev-parse','HEAD^{tree}');before=source_manifest();dirty_before=dirty()
run=os.getenv('GITHUB_RUN_ID','local-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
attempt=os.getenv('GITHUB_RUN_ATTEMPT','1')
report=dict(schema_version=1,sha=sha,tree_sha=tree,run_id=run,attempt=attempt,repository=os.getenv('GITHUB_REPOSITORY'),started_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),exact_commit=not bool(dirty_before),stages=[],limitations=['Single-core basic-task subset; no full OSEK/BCC/SC1/AUTOSAR conformance','Generic Lean model and bounded generated-C target adapter are compared by tests; no compiler/adapter/assembly refinement proof','No liveness, WCET, full IRQ or resource-subsystem proof','Source snapshot checked at beginning/end; not an adversarial concurrent-write monitor'],source_hashes=before)
def flush():
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
def stage(name,cmd,requires=()):
    prior={s['name']:s['status'] for s in report['stages']}
    row=dict(name=name,command=cmd,status='not_run',returncode=None,log=name+'.log')
    if any(prior.get(k)!='passed' for k in requires):
        row['reason']='dependency failed or not run';(out/row['log']).write_text(row['reason']+'\n')
    else:
        start=time.monotonic()
        try:
            x=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=240)
            (out/row['log']).write_text(x.stdout)
            row.update(returncode=x.returncode,status='passed' if x.returncode==0 else 'failed')
        except (OSError,subprocess.TimeoutExpired) as e:
            partial=e.stdout if isinstance(e,subprocess.TimeoutExpired) else ''
            if isinstance(partial,bytes):partial=partial.decode(errors='replace')
            (out/row['log']).write_text((partial or '')+'\n'+str(e)+'\n')
            row.update(status='failed',reason=str(e))
        row['seconds']=round(time.monotonic()-start,3)
    report['stages'].append(row);flush();print(name+': '+row['status'],flush=True)
    return row['status']=='passed'
flush()
if dirty_before and not a.allow_dirty:
    report['stages']=[dict(name='source-identity',status='failed',reason='working tree is not exact HEAD')];flush();raise SystemExit(1)
# Only generated build directories belonging to this project are removed.
for path in ['build','.lake/build']:
    if pathlib.Path(path).exists():shutil.rmtree(path)
pathlib.Path('build').mkdir()
stage('lean-version',['lean','--version'])
stage('compiler-version',['gcc','--version'])
stage('lean-build',['lake','build'],['lean-version'])
stage('prepare-audit',['python3','scripts/lean_declarations.py','build/AuditAll.lean'],['lean-build'])
stage('axioms',['lake','env','lean','build/AuditAll.lean'],['prepare-audit'])
stage('axiom-audit',['python3','scripts/audit.py',str(out)],['axioms'])
stage('generate-model',['lake','env','lean','-c','build/Model.c','LeanCpOs/Model.lean'],['lean-build'])
stage('generate-bridge',['lake','env','lean','-c','build/Bridge.c','LeanCpOs/Bridge.lean'],['lean-build'])
stage('generate-task-scalar',['lake','env','lean','-c','build/TaskScalar.c','LeanCpOs/Task/Scalar.lean'],['lean-build'])
stage('compile-model',['leanc','-O2','-fstack-usage','-c','build/Model.c','-o','build/Model.o'],['generate-model'])
stage('compile-bridge',['leanc','-O2','-fstack-usage','-c','build/Bridge.c','-o','build/Bridge.o'],['generate-bridge'])
stage('compile-task-scalar',['leanc','-O2','-fstack-usage','-c','build/TaskScalar.c','-o','build/TaskScalar.o'],['generate-task-scalar'])
try:prefix=subprocess.check_output(['lean','--print-prefix'],text=True).strip()
except Exception:prefix='__unavailable__'
for name,source in [('host','c/host.c'),('control','c/control_flow.c')]:
    stage('compile-'+name,['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-fstack-usage','-I'+prefix+'/include','-Ic','-c',source,'-o','build/'+name+'.o'],['lean-build'])
    stage('link-'+name,['leanc','-O2','build/'+name+'.o','build/Model.o','build/Bridge.o','-o','build/'+('c-host' if name=='host' else 'control-flow')],['compile-'+name,'compile-model','compile-bridge'])
stage('host-and-c-tests',['python3','tests/test_differential.py',str(out/'test-results')],['link-host'])
stage('control-flow',['build/control-flow'],['link-control'])
stage('compile-task-scalar-host',['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-c','c/task_scalar_host.c','-o','build/task-scalar-host.o'],['lean-build'])
stage('link-task-scalar-host',['leanc','-O2','build/task-scalar-host.o','build/TaskScalar.o','-o','build/task-scalar-host'],['compile-task-scalar-host','compile-task-scalar'])
stage('task-control',['python3','tests/test_task_control.py',str(out/'test-results'),'--scalar-runner','build/task-scalar-host'],['link-task-scalar-host'])
stage('qemu-task-control',['python3','scripts/verify_qemu.py',str(out/'qemu')],['lean-build'])
stage('runtime-audit',['python3','scripts/runtime_audit.py',str(out)],['compile-model','compile-bridge','compile-task-scalar'])
stage('symbols',['nm','--defined-only','build/c-host'],['link-host'])
stage('evidence-selftests',['python3','tests/test_evidence.py'])
stage('trace',['python3','scripts/trace_check.py',str(out)])
# Preserve actual generated C, compiler frame reports and linked binaries.
for src in ['build','.lake/build/lib/lean']:
    if pathlib.Path(src).exists():shutil.copytree(src,out/('generated' if src=='build' else 'olean'),dirs_exist_ok=True)
shutil.copytree('trace',out/'trace-inputs',dirs_exist_ok=True)
toolchain={}
for exe in ['lean','lake','leanc','gcc']:
    path=shutil.which(exe)
    if path:toolchain[exe]=dict(sha256=digest(pathlib.Path(path).resolve()))
# Record packaged compiler/runtime without pretending these are proved correct.
for rel in ['bin/clang','bin/ld.lld','include/lean/lean.h','lib/lean/libleanshared.so','lib/lean/libleanrt.a','lib/lean/libInit.a']:
    path=pathlib.Path(prefix)/rel
    if path.is_file():toolchain[rel]=dict(sha256=digest(path))
compat=os.getenv('LD_PRELOAD')
if compat:
    toolchain['host_environment_adaptation']=[dict(name=pathlib.Path(x).name,sha256=digest(x)) for x in compat.split(':') if pathlib.Path(x).is_file()]
for name in ['LICENSE', 'LICENSES']:
    path=pathlib.Path(prefix)/name
    if path.is_file():
        (out/'runtime-notices').mkdir(exist_ok=True);shutil.copy2(path,out/'runtime-notices'/name)
report['toolchain']=toolchain;report['platform']=dict(system=platform.system(),machine=platform.machine())
after=source_manifest();stable=before==after and dirty_before==dirty() and sha==git('rev-parse','HEAD')
report['source_unchanged']=stable
report['stages'].append(dict(name='source-stability',status='passed' if stable else 'failed'))
report['overall']='passed' if stable and all(x['status']=='passed' for x in report['stages']) else 'failed'
report['coverage']='incomplete';report['finished_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
report['artifact_files']={str(p.relative_to(out)):digest(p) for p in sorted(out.rglob('*')) if p.is_file() and p.name not in ['report.json','index.html','SHA256SUMS']}
flush()
subprocess.run(['python3','scripts/render_report.py',str(out)],check=True)
(out/'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.relative_to(out)}\n' for p in sorted(out.rglob('*')) if p.is_file() and p.name!='SHA256SUMS'))
print(json.dumps({k:report[k] for k in ['sha','run_id','exact_commit','source_unchanged','overall','coverage']},indent=2))
raise SystemExit(0 if report['overall']=='passed' else 1)
