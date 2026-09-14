import json,subprocess,sys
out=[];page=1
while True:
    r=subprocess.run(['gh','api',f'repos/digitalpalidictionary/dpd-db/issues?state=all&per_page=100&page={page}'],capture_output=True,text=True)
    d=json.loads(r.stdout)
    if not d: break
    for i in d:
        if 'pull_request' in i: continue
        out.append({'number':i['number'],'node_id':i['node_id'],'state':i['state'],
            'title':i['title'],
            'labels':[l['name'] for l in i['labels']],
            'type':(i.get('type') or {}).get('name'),
            'fields':{f['issue_field_name']:(f.get('single_select_option') or {}).get('name',f.get('value')) for f in i.get('issue_field_values',[])}})
    page+=1
json.dump(out,open(sys.argv[1],'w'),indent=1)
print(len(out),'issues snapshotted')
