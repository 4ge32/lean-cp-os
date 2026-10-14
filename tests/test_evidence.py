#!/usr/bin/env python3
"""Exercise actual SHA enumeration and missing historical verifier behavior."""
import json,os,pathlib,subprocess,tempfile
root=pathlib.Path(__file__).resolve().parents[1]
enumerate_script=root/'scripts/enumerate_commits.py';verify_script=root/'scripts/verify_commits.py'
with tempfile.TemporaryDirectory(prefix='lcpo-evidence-test-') as tmp:
    repo=pathlib.Path(tmp)/'repo';repo.mkdir()
    def git(*args):return subprocess.check_output(['git',*args],cwd=repo,text=True).strip()
    git('init','-b','main');git('config','user.name','Evidence Test');git('config','user.email','test@example.invalid')
    shas=[]
    for i in range(3):
        (repo/'sample').write_text(str(i));git('add','sample');git('commit','-m','fixture '+str(i));shas.append(git('rev-parse','HEAD'))
    env=os.environ.copy();env.update(GITHUB_EVENT_NAME='push',GITHUB_RUN_ID='fixture',GITHUB_RUN_ATTEMPT='1')
    for name,before,expected in [('batch',shas[0],shas[1:]),('first','0'*40,shas),('missing','f'*40,shas)]:
        event=pathlib.Path(tmp)/(name+'.json');event.write_text(json.dumps({'before':before,'after':shas[-1]}));env['GITHUB_EVENT_PATH']=str(event)
        out=pathlib.Path(tmp)/name
        subprocess.run(['python3',str(enumerate_script),str(out)],cwd=repo,env=env,check=True,stdout=subprocess.DEVNULL)
        plan=json.loads((out/'targets.json').read_text());assert plan['targets']==expected,(name,plan)
        for sha in expected:
            rec=json.loads((out/'commits'/sha/'runs/fixture-1/execution.json').read_text());assert rec['status']=='not_run'
        if name=='batch':
            p=subprocess.run(['python3',str(verify_script),str(out)],cwd=repo,env=env,stdout=subprocess.DEVNULL)
            assert p.returncode==1
            records=[json.loads(f.read_text()) for f in out.glob('commits/*/runs/*/execution.json')]
            assert len(records)==2 and all(x['status']=='not_run' and 'predates' in x['reason'] for x in records)
        print('PASS evidence scenario:',name, len(expected),'SHAs')
    env['GITHUB_EVENT_NAME']='workflow_dispatch'
    for name,inputs,expected in [('manual-default',{},[shas[-1]]),('manual-head',{'scope':'head'},[shas[-1]]),('manual-history',{'scope':'history'},shas)]:
        event=pathlib.Path(tmp)/(name+'.json');event.write_text(json.dumps({'inputs':inputs}));env['GITHUB_EVENT_PATH']=str(event)
        out=pathlib.Path(tmp)/name
        subprocess.run(['python3',str(enumerate_script),str(out)],cwd=repo,env=env,check=True,stdout=subprocess.DEVNULL)
        plan=json.loads((out/'targets.json').read_text());assert plan['targets']==expected,(name,plan)
        assert plan['scope']==inputs.get('scope','head')
        records=list(out.glob('commits/*/runs/fixture-1/execution.json'))
        assert len(records)==len(expected)
        assert all(json.loads(f.read_text())['status']=='not_run' for f in records)
        print('PASS evidence scenario:',name,len(expected),'SHAs')
print('PASS T-EVIDENCE: historical SHAs stay not_run; batch push does not collapse to HEAD')
