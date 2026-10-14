#!/usr/bin/env python3
"""Enumerate every introduced commit, never use only the push payload's head."""
import json,os,pathlib,re,subprocess,sys
out=pathlib.Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
event=json.load(open(os.environ['GITHUB_EVENT_PATH']));kind=os.environ['GITHUB_EVENT_NAME'];warnings=[]
scope=event.get('inputs',{}).get('scope','head') if kind=='workflow_dispatch' else 'history'
if scope not in ['head','history']:raise ValueError('Invalid verification scope')
def git(*a):return subprocess.check_output(['git',*a],text=True).strip()
def valid(sha):
    if not re.fullmatch('[0-9a-f]{40}',sha):raise ValueError('not a full SHA')
    return sha
if kind=='push':
    after=valid(event['after']);before=valid(event['before'])
elif kind=='pull_request':
    after=valid(event['pull_request']['head']['sha']);before=valid(event['pull_request']['base']['sha'])
else:
    after=valid(git('rev-parse','HEAD'));before='0'*40
if after=='0'*40:targets=[];warnings.append('Branch deletion: no target commit')
elif scope=='head':targets=[after]
else:
    if before!='0'*40:
        try:git('cat-file','-e',before+'^{commit}')
        except subprocess.CalledProcessError:
            warnings.append('before SHA unavailable; verifying all reachable history, not silently substituting HEAD')
            before='0'*40
    selection=after if before=='0'*40 else before+'..'+after
    targets=git('rev-list','--reverse','--topo-order',selection).splitlines()
    if not targets:targets=[after];warnings.append('Empty range: verify after SHA explicitly')
plan=dict(event=kind,scope=scope,before=before,after=after,targets=targets,warnings=warnings,run_id=os.environ.get('GITHUB_RUN_ID','local'),attempt=os.environ.get('GITHUB_RUN_ATTEMPT','1'))
(out/'targets.json').write_text(json.dumps(plan,indent=2)+'\n')
# Persist every not-run record BEFORE setup or verification, so interruption is visible.
for sha in targets:
    d=out/'commits'/sha/'runs'/(plan['run_id']+'-'+plan['attempt']);d.mkdir(parents=True,exist_ok=True)
    (d/'execution.json').write_text(json.dumps(dict(sha=sha,status='not_run',reason='queued; may remain not_run if setup/job cancelled',run_id=plan['run_id'],attempt=plan['attempt']),indent=2)+'\n')
print(json.dumps(plan,indent=2))
