#!/usr/bin/env python3
"""Trusted-main-only publisher. Merge immutable lightweight evidence history.
Binaries/olean files stay in the run-specific Actions artifact (90-day retention).
No credentials or private context are written to the published tree.
"""
import base64,html,json,os,pathlib,shutil,subprocess,sys
src=pathlib.Path(sys.argv[1]).resolve();site=pathlib.Path(sys.argv[2]).resolve()
repo=os.environ['GITHUB_REPOSITORY'];token=os.environ['GH_TOKEN']
env=os.environ.copy();env.update(GIT_CONFIG_COUNT='1',GIT_CONFIG_KEY_0='http.https://github.com/.extraheader',GIT_CONFIG_VALUE_0='AUTHORIZATION: basic '+base64.b64encode(('x-access-token:'+token).encode()).decode())
url='https://github.com/'+repo+'.git'
def git(*args,cwd=None,check=True):return subprocess.run(['git',*args],cwd=cwd,env=env,check=check,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
def publish_once():
    # Failure to read an existing history must not overwrite it with an empty tree.
    refs=git('ls-remote',url,'refs/heads/evidence-history')
    if refs.stdout.strip():git('clone','--depth','1','--branch','evidence-history',url,str(site))
    else:
        site.mkdir(parents=True,exist_ok=True);git('init','-b','evidence-history',cwd=site);git('remote','add','origin',url,cwd=site)
    plan=json.loads((src/'targets.json').read_text());run=plan['run_id']+'-'+plan['attempt']
    runpath=site/'runs'/run
    if runpath.exists():raise SystemExit('Immutable run history already exists; refusing overwrite')
    runpath.mkdir(parents=True);shutil.copy2(src/'targets.json',runpath/'targets.json')
    for file in (src/'commits').rglob('*'):
        if file.is_file() and (file.suffix in ['.json','.html','.log','.txt','.stdout','.stderr','.c','.su'] or file.name in ['SHA256SUMS','LICENSE','LICENSES']):
            # .olean/.ilean and binaries deliberately stay in the Actions artifact.
            dest=site/'commits'/file.relative_to(src/'commits');dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists():raise SystemExit('Refusing to overwrite prior evidence: '+str(dest))
            shutil.copy2(file,dest)
    plans=[json.loads(f.read_text()) for f in (site/'runs').glob('*/targets.json')]
    latest_plan=max(plans,key=lambda p:(int(p['run_id']),int(p['attempt'])))
    latest_run=latest_plan['run_id']+'-'+latest_plan['attempt']
    latest=dict(sha=latest_plan['after'],run_id=latest_plan['run_id'],attempt=latest_plan['attempt'],path='commits/'+latest_plan['after']+'/runs/'+latest_run+'/index.html',coverage='incomplete')
    (site/'latest.json').write_text(json.dumps(latest,indent=2)+'\n')
    rows=[]
    for f in sorted((site/'commits').glob('*/runs/*/execution.json')):
        x=json.loads(f.read_text());page=f.parent/'index.html';rel=page.relative_to(site) if page.exists() else f.relative_to(site)
        rows.append('<tr><td><code>'+html.escape(x['sha'])+'</code></td><td>'+html.escape(x['run_id']+' / '+x['attempt'])+'</td><td>'+html.escape(x['status'])+'</td><td><a href="'+str(rel)+'">Evidence</a></td></tr>')
    (site/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>Lean CP OS verification history</title><style>body{font:16px system-ui;max-width:1200px;margin:40px auto;padding:20px;background:#101820;color:#edf5ff}a{color:#80cfff}td,th{padding:12px;border:1px solid #506070}table{border-collapse:collapse}code{overflow-wrap:anywhere}</style><h1>Lean CP OS verification history</h1><p>Every recorded SHA and run remains separate. Gate success is not complete OS verification.</p><p>Latest recorded main run SHA: <code>'+html.escape(latest['sha'])+'</code> · <a href="latest.json">latest pointer</a></p><p>Full binaries and hashes: run-specific GitHub Actions artifacts, retained 90 days. This site keeps lightweight history.</p><table><tr><th>SHA</th><th>Run / attempt</th><th>Status</th><th>Report</th></tr>'+''.join(rows)+'</table>')
    (site/'.nojekyll').write_text('')
    git('config','user.name','github-actions[bot]',cwd=site);git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com',cwd=site)
    git('add','.',cwd=site);git('commit','-m','Archive verification run '+run,cwd=site)
    result=git('push','origin','HEAD:refs/heads/evidence-history',cwd=site,check=False)
    if result.returncode:
        if any(x in result.stderr for x in ['fetch first','non-fast-forward']):
            raise RuntimeError('concurrent-history-update')
        raise RuntimeError('History push failed; inspect GitHub permissions/network')
    # Do not upload git metadata or repository credentials to Pages.
    shutil.rmtree(site/'.git')

if site.exists():raise SystemExit('Output site path already exists')
for retry in range(6):
    try:
        publish_once()
        break
    except RuntimeError as e:
        if str(e)!='concurrent-history-update' or retry==5:raise
        # This path is freshly created by this invocation, never a user checkout.
        shutil.rmtree(site)
else:
    raise SystemExit('Could not append history after concurrent pushes')
