"""Restore issue types / Priority / Effort to a snapshot's state. Labels untouched unless --labels."""
import json,subprocess,sys
TID={'Bug':'IT_kwDOBd2Dd84A-nhW','Feature':'IT_kwDOBd2Dd84A-nhZ','Task':'IT_kwDOBd2Dd84A-nhR'}
FID={'Priority':'IFSS_kgDOAUgLjQ','Effort':'IFSS_kgDOAUgLkA'}
OPT={'Priority':{'Urgent':'IFSSO_kgDOAj3-RQ','High':'IFSSO_kgDOAj3-Rg','Medium':'IFSSO_kgDOAj3-Rw','Low':'IFSSO_kgDOAj3-SA'},
     'Effort':{'High':'IFSSO_kgDOAj3-SQ','Medium':'IFSSO_kgDOAj3-Sg','Low':'IFSSO_kgDOAj3-Sw'}}
def gql(q,**v):
    cmd=['gh','api','graphql','-f','query='+q]+[x for k,val in v.items() for x in ('-f',f'{k}={val}')]
    r=subprocess.run(cmd,capture_output=True,text=True)
    if r.returncode or '"errors"' in r.stdout: raise RuntimeError(r.stdout+r.stderr)
CLEAR_T='mutation($i:ID!){updateIssue(input:{id:$i,issueTypeId:null}){issue{number}}}'
SET_T='mutation($i:ID!,$t:ID!){updateIssue(input:{id:$i,issueTypeId:$t}){issue{number}}}'
SET_V='mutation($i:ID!,$f:ID!,$o:ID!){setIssueFieldValue(input:{issueId:$i,issueFields:[{fieldId:$f,singleSelectOptionId:$o,suggest:false}]}){issue{number}}}'
DEL_V='mutation($i:ID!,$f:ID!){setIssueFieldValue(input:{issueId:$i,issueFields:[{fieldId:$f,delete:true}]}){issue{number}}}'
snap=json.load(open(sys.argv[1])); dry='--dry' in sys.argv; n=0
for it in snap:
    acts=[]
    acts.append(('type',it['type']))
    for f in ('Priority','Effort'): acts.append((f,it['fields'].get(f)))
    n+=1
    if dry: continue
    for kind,val in acts:
        if kind=='type':
            gql(SET_T,i=it['node_id'],t=TID[val]) if val else gql(CLEAR_T,i=it['node_id'])
        else:
            gql(SET_V,i=it['node_id'],f=FID[kind],o=OPT[kind][val]) if val else gql(DEL_V,i=it['node_id'],f=FID[kind])
print(('DRY ' if dry else '')+f'{n} issues restored')
