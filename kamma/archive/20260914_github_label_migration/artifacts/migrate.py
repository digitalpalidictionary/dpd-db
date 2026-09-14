import json,subprocess,sys
TYPE={'1-bug':'IT_kwDOBd2Dd84A-nhW','1-enhancement':'IT_kwDOBd2Dd84A-nhZ',
      '1-refactor':'IT_kwDOBd2Dd84A-nhR','1-chore':'IT_kwDOBd2Dd84A-nhR'}
TNAME={'IT_kwDOBd2Dd84A-nhW':'Bug','IT_kwDOBd2Dd84A-nhZ':'Feature','IT_kwDOBd2Dd84A-nhR':'Task'}
PRIO_F='IFSS_kgDOAUgLjQ'
PRIO={'p1':'IFSSO_kgDOAj3-RQ','p2':'IFSSO_kgDOAj3-Rg','p3':'IFSSO_kgDOAj3-Rw','p4':'IFSSO_kgDOAj3-SA'}
EFF_F='IFSS_kgDOAUgLkA'
EFF={'t1':'IFSSO_kgDOAj3-Sw','t2':'IFSSO_kgDOAj3-Sg','t3':'IFSSO_kgDOAj3-SQ','t4':'IFSSO_kgDOAj3-SQ'}

def gql(q,**v):
    cmd=['gh','api','graphql','-f','query='+q]
    for k,val in v.items(): cmd+=['-f',f'{k}={val}']
    r=subprocess.run(cmd,capture_output=True,text=True)
    d=json.loads(r.stdout or '{}')
    if 'errors' in d or r.returncode: raise RuntimeError(r.stdout+r.stderr)
    return d

SET_TYPE='mutation($i:ID!,$t:ID!){updateIssue(input:{id:$i,issueTypeId:$t}){issue{number issueType{name}}}}'
SET_VAL='mutation($i:ID!,$f:ID!,$o:ID!){setIssueFieldValue(input:{issueId:$i,issueFields:[{fieldId:$f,singleSelectOptionId:$o,suggest:false}]}){issue{number}}}'

issues=json.load(open(sys.argv[1]))
only=sys.argv[3] if len(sys.argv)>3 else None
dry='--dry' in sys.argv
done=[]
for it in issues:
    if only and str(it['number'])!=only: continue
    ls=[l['name'] for l in it['labels']['nodes']]
    acts=[]
    t=[TYPE[x] for x in ls if x in TYPE]
    if t and not it.get('issueType'): acts.append(('type',t[0]))
    p=[PRIO[x] for x in ls if x in PRIO]
    if p: acts.append(('prio',p[0]))
    e=[EFF[x] for x in ls if x in EFF]
    if e: acts.append(('eff',e[0]))
    if not acts: continue
    if len([x for x in ls if x in PRIO])>1: print('!! multi-priority on',it['number'],ls)
    for kind,val in acts:
        if dry: continue
        if kind=='type': gql(SET_TYPE,i=it['id'],t=val)
        else: gql(SET_VAL,i=it['id'],f=PRIO_F if kind=='prio' else EFF_F,o=val)
    done.append((it['number'],[k for k,_ in acts]))
print(('DRY ' if dry else '')+f'{len(done)} issues touched')
