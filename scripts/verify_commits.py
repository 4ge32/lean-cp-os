#!/usr/bin/env python3
import json,os,pathlib,subprocess,sys
root=pathlib.Path.cwd();out=pathlib.Path(sys.argv[1]).resolve();plan=json.loads((out/'targets.json').read_text());failed=False
for sha in plan['targets']:
    target=out/'commits'/sha/'runs'/(plan['run_id']+'-'+plan['attempt'])
    work=root.parent/('verify-'+sha)
    created=False
    record=dict(sha=sha,status='not_run',run_id=plan['run_id'],attempt=plan['attempt'])
    try:
        if work.exists():raise RuntimeError('Refusing existing worktree path')
        subprocess.run(['git','worktree','add','--detach',str(work),sha],check=True)
        created=True
        if not (work/'scripts/verify.py').exists():
            record['reason']='This historical SHA predates the verifier; not verified by a newer tree';failed=True
        else:
            p=subprocess.run(['python3','scripts/verify.py','--out',str(target)],cwd=work,timeout=600)
            record.update(status='passed' if p.returncode==0 else 'failed',returncode=p.returncode)
            failed |= p.returncode!=0
    except Exception as e:
        record.update(status='failed',reason=str(e));failed=True
    finally:
        (target/'execution.json').write_text(json.dumps(record,indent=2)+'\n')
        if created:subprocess.run(['git','worktree','remove','--force',str(work)],check=False)
    print(json.dumps(record),flush=True)
sys.exit(1 if failed else 0)
