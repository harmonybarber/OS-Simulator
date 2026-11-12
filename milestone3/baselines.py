import json
from engine.process import simulate
from engine.memory import simulate_memory
from engine.filesystem import FileSystem

def run_baselines(directory):
    rows=[]
    for name in ('process','memory','file'):
        with open(directory/f'{name}_baseline.json',encoding='utf-8') as f: fixture=json.load(f)
        if name=='process':
            r=simulate(fixture['input']['processes'],fixture['input']['algorithm'],fixture['input'].get('quantum',4))
            actual={'gantt':r['gantt'],'processes':r['processes'],'metrics':r['metrics']}
        elif name=='memory':
            actual={k:v for k,v in simulate_memory(**fixture['input']).items() if k!='trace'}
        else:
            fs=FileSystem();outputs=[]
            for op in fixture['input']['operations']:outputs.append(fs.execute(**op))
            actual={'outputs':outputs,'stats':fs.stats(),'entries':fs.entries}
        expected=fixture['expected']
        rows.append({'test':name,'expected':json.dumps(expected,sort_keys=True),
                     'actual':json.dumps(actual,sort_keys=True),'status':'PASS' if expected==actual else 'FAIL'})
    return rows
