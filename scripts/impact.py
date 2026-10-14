#!/usr/bin/env python3
"""Conservative module/file-level impact; does not claim semantic minimality."""
import json,subprocess,sys
req=json.load(open('trace/requirements.json'))['requirements']
changed=subprocess.check_output(['git','diff','--name-only',sys.argv[1],'HEAD'],text=True).splitlines()
all_change=any(x.startswith(('trace/','scripts/','.github/')) or x in ['lean-toolchain','lakefile.toml','lake-manifest.json'] for x in changed)
rows=[r for r in req if all_change or set(changed)&set(r['files']+r['boundaries'])]
print(json.dumps(dict(changed_files=changed,conservative=True,requirements=[r['id'] for r in rows],theorems=sorted({t for r in rows for t in r['theorems']}),tests=sorted({t for r in rows for t in r['tests']})),indent=2))
