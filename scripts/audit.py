#!/usr/bin/env python3
import json,pathlib,re,sys
from lean_declarations import declarations
out=pathlib.Path(sys.argv[1]); text=(out/'axioms.log').read_text()
src='\n'.join(p.read_text() for p in pathlib.Path('.').glob('**/*.lean') if '.lake' not in p.parts and 'build' not in p.parts)
# No project axioms, opaque proof bypass, native_decide, or admitted goals.
for token in [r'\bsorry\b',r'\badmit\b',r'^\s*axiom\b',r'\bnative_decide\b',r'\bimplemented_by\b']:
    if re.search(token,src,re.M): raise SystemExit('Forbidden proof construct: '+token)
names=[row['name'] for row in declarations() if row['kind']=='theorem']
rows=[]
for full in names:
    no=f"'{full}' does not depend on any axioms"
    m=re.search(re.escape("'"+full+"' depends on axioms: [")+r'([^\]]*)\]',text)
    if no in text: deps=[]
    elif m: deps=[x.strip() for x in m[1].split(',') if x.strip()]
    else: raise SystemExit('Missing audit output for '+full)
    if set(deps)-{'propext'}: raise SystemExit('Unexpected axiom dependencies '+repr(deps))
    rows.append(dict(theorem=full,axioms=deps,status='checked'))
(out/'axioms.json').write_text(json.dumps(dict(allowed=['propext'],theorems=rows),indent=2)+'\n')
print(f'PASS: {len(rows)} theorems; only propositional extensionality allowed; every dependency listed')
