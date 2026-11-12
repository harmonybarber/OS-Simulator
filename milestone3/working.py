import json
import streamlit as st
import pandas as pd
from engine.process import Process, simulate, ALGORITHMS
from engine.memory import simulate_memory
from engine.filesystem import FileSystem
from engine.parallel import simulate_parallel
from engine.synchronization import demonstrate, race_demo, detect_deadlock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = [{'pid':'P1','arrival':0,'burst':8,'priority':2}, {'pid':'P2','arrival':1,'burst':4,'priority':1}, {'pid':'P3','arrival':2,'burst':2,'priority':3}, {'pid':'P4','arrival':4,'burst':5,'priority':2}]

def init():
    for k,v in [('workload',DEFAULT),('result',None),('memory_result',None),('fs',None),('parallel_result',None),('test_rows',[]),('scenario_name','Baseline Scenario')]:
        if k not in st.session_state: st.session_state[k] = v if k != 'workload' else [dict(p) for p in v]
    if st.session_state.fs is None: st.session_state.fs=FileSystem()

def chart(segments, multicore=False):
    if not segments:return
    df=pd.DataFrame(segments)
    df['Duration']=df['end']-df['start']
    df['Lane']=df['core'].map(lambda c:f'Core {c+1}') if multicore else 'CPU'
    df['Task']=df['pid']
    # Plotly timeline expects datetimes; numeric ms must be drawn as rectangles instead.
    import plotly.graph_objects as go
    fig=go.Figure()
    for _,s in df.iterrows():
        fig.add_trace(go.Bar(x=[s['Duration']],y=[s['Lane']],base=[s['start']],orientation='h',name=s['Task'],
                             legendgroup=s['Task'],showlegend=not any(tr.name==s['Task'] for tr in fig.data),
                             hovertemplate=f"{s['Task']}: {s['start']}–{s['end']} ms<extra></extra>"))
    fig.update_layout(barmode='overlay',xaxis_title='Time (ms)',yaxis_title='',height=max(240,100+80*df.Lane.nunique()),
                      paper_bgcolor='#20252E',plot_bgcolor='#20252E',font_color='#D6D9E0')
    st.plotly_chart(fig,use_container_width=True)

def process_page():
    init();st.header('Process Manager');st.caption('Deterministic scheduling simulation with process states and real metrics.')
    a,b,c,d=st.columns(4)
    with a: algo=st.selectbox('Scheduling Algorithm',ALGORITHMS)
    with b: quantum=int(st.number_input('Quantum (ms)',min_value=1,value=4))
    with c: aging=int(st.number_input('Aging interval (ms)',min_value=1,value=5))
    with d: cost=int(st.number_input('Context switch cost (ms)',min_value=0,value=0))
    st.subheader('Workload');st.caption('Edit processes directly. Optional I/O fields: io_start, io_duration.')
    edited=st.data_editor(pd.DataFrame(st.session_state.workload),num_rows='dynamic',use_container_width=True,key='process_editor')
    x,y=st.columns(2)
    with x: run=st.button('▶ Run Process Simulation',type='primary')
    with y: reset=st.button('Reset Process Manager')
    if reset:st.session_state.workload=[dict(p) for p in DEFAULT];st.session_state.result=None;st.rerun()
    if run:
        try:
            records=edited.where(pd.notnull(edited),None).to_dict('records')
            processes=[Process(pid=str(p['pid']),arrival=int(p['arrival']),burst=int(p['burst']),priority=int(p['priority']),
                               io_start=int(p['io_start']) if p.get('io_start') is not None else None,
                               io_duration=int(p.get('io_duration') or 0)) for p in records]
            st.session_state.workload=[vars(p) for p in processes]
            st.session_state.result=simulate(processes,algo,quantum,aging,cost)
        except (ValueError,TypeError,KeyError) as exc:st.error(f'Invalid workload: {exc}')
    result=st.session_state.result
    if result:
        m=result['metrics'];st.subheader(f"Results — {result['algorithm']}")
        cols=st.columns(4)
        for col,(label,value) in zip(cols,[('CPU Utilization',f"{m['cpu_utilization']:.2f}%"),('Throughput',f"{m['throughput']:.4f} jobs/ms"),('Context Switches',str(m['context_switches'])),('Makespan',f"{m['makespan']} ms")]):col.metric(label,value)
        cols=st.columns(3)
        for col,(label,key) in zip(cols,[('Average Waiting','avg_waiting'),('Average Response','avg_response'),('Average Turnaround','avg_turnaround')]):col.metric(label,f"{m[key]:.2f} ms")
        st.subheader('CPU Gantt Chart');chart(result['gantt'])
        st.subheader('Process Table');st.dataframe(pd.DataFrame(result['processes']),use_container_width=True,hide_index=True)
        st.subheader('Ready Queue and Process States')
        index=st.slider('Inspect simulation at time (ms)',0,max(0,len(result['snapshots'])-1),0)
        snap=result['snapshots'][index]
        st.write(f"**Running:** {snap['running']} | **Ready queue:** {', '.join(snap['ready']) or '(empty)'}")
        st.dataframe(pd.DataFrame([{'pid':pid,'state':state} for pid,state in snap['states'].items()]),hide_index=True)
        with st.expander('Deterministic event log'):st.dataframe(pd.DataFrame(result['events']),hide_index=True)

def memory_page():
    init();st.header('Memory Manager');a,b,c=st.columns(3)
    with a:policy=st.selectbox('Page Replacement Policy',['FIFO','LRU'])
    with b:size=int(st.number_input('Page Size',min_value=1,value=4096))
    with c:frames=int(st.number_input('Frames',min_value=1,value=4))
    addresses=st.text_area('Addresses (decimal or 0x hex)',value='0x0040\n0x10A0\n0x0044\n0x20B0')
    if st.button('Run Memory Test'):
        try:st.session_state.memory_result=simulate_memory([int(s.strip(),0) if s.strip().lower().startswith('0x') else int(s.strip()) for s in addresses.splitlines() if s.strip()],size,frames,policy)
        except ValueError as exc:st.error(str(exc))
    if st.button('Reset Memory Manager'):st.session_state.memory_result=None
    r=st.session_state.memory_result
    if r:
        cols=st.columns(4)
        for col,k in zip(cols,['references','hits','faults','evictions']):col.metric(k.title(),r[k])
        st.dataframe(pd.DataFrame(r['trace']),use_container_width=True,hide_index=True)

def file_page():
    init();st.header('File Manager');fs=st.session_state.fs
    cmd=st.selectbox('Command',['mkdir','ls','mkfile','write','append','cat','rm','rmdir'])
    path=st.text_input('Path','/docs/notes.txt');content=st.text_area('Content')
    if st.button('Execute Command'):
        try:st.success(str(fs.execute(cmd,path,content)))
        except ValueError as exc:st.error(str(exc))
    if st.button('Reset File Manager'):st.session_state.fs=FileSystem();st.rerun()
    st.subheader('File Tree');st.code('\n'.join(f"{p} ({v['type']})" for p,v in sorted(fs.entries.items())))
    st.subheader('Statistics');st.json(fs.stats())
    st.subheader('Operation Log');st.dataframe(pd.DataFrame(fs.log),hide_index=True)

def parallel_page():
    init();st.header('Parallel Computing');a,b=st.columns(2)
    with a:cores=st.selectbox('Number of cores',[1,2,4])
    with b:policy=st.selectbox('Workload Distribution',['Global Ready Queue','Round-Robin Assignment','Least-Loaded Assignment'])
    if st.button('Run Parallel Test',type='primary'):
        try:st.session_state.parallel_result=simulate_parallel(st.session_state.workload,cores,policy)
        except ValueError as exc:st.error(str(exc))
    if st.button('Compare Sequential vs Parallel'):
        try:
            st.dataframe(pd.DataFrame([{'cores':n,**{k:v for k,v in simulate_parallel(st.session_state.workload,n,policy).items() if k in ('parallel_time','speedup','efficiency','load_balance')}} for n in (1,2,4)]),hide_index=True)
        except ValueError as exc:st.error(str(exc))
    if st.button('Reset Parallel Test'):st.session_state.parallel_result=None
    r=st.session_state.parallel_result
    if r:
        cols=st.columns(4)
        for col,label,value in zip(cols,['Sequential Time','Parallel Time','Speedup','Efficiency'],[f"{r['sequential_time']} ms",f"{r['parallel_time']} ms",f"{r['speedup']:.2f}x",f"{r['efficiency']:.1f}%"]):col.metric(label,value)
        st.metric('Load Balance (min/max busy time)',f"{r['load_balance']:.2f}")
        st.subheader('Multicore Gantt Chart');chart(r['gantt'],True)
        st.dataframe(pd.DataFrame([{'core':i+1,'assignments':', '.join(jobs),'utilization':f'{r["per_core_utilization"][i]:.1f}%'} for i,jobs in enumerate(r['assignments'])]),hide_index=True)
    st.subheader('Synchronization Demonstration')
    method=st.selectbox('Method',['Mutex / Lock','Semaphore','Barrier'])
    mode=st.selectbox('Mode',['Synchronized','Unsafe Race Demonstration'])
    if st.button('Run Synchronization Demo'):
        st.json(demonstrate(method,cores) if mode=='Synchronized' else race_demo(cores))
    st.subheader('Deadlock Detection (single-instance wait-for graph)')
    edges=st.text_area('Wait-for edges, one per line (e.g. P1,P2)','P1,P2\nP2,P1')
    if st.button('Detect Deadlock'):
        try:st.warning('Cycle detected: deadlock' if detect_deadlock([tuple(x.strip() for x in line.split(',')) for line in edges.splitlines() if line.strip()]) else 'No cycle detected')
        except ValueError as exc:st.error(str(exc))

def scenario_page():
    init();st.header('Scenario Builder');name=st.text_input('Scenario Name',st.session_state.scenario_name)
    st.caption('JSON process workload; supports optional io_start and io_duration.')
    content=st.text_area('Processes (JSON)',json.dumps(st.session_state.workload,indent=2),height=240)
    upload=st.file_uploader('Load saved scenario JSON',type=['json'])
    if upload:
        try:
            obj=json.load(upload);data=obj['processes'];simulate(data,obj.get('algorithm','FCFS'))
            st.session_state.workload=data;st.session_state.scenario_name=obj.get('name','Imported');st.success('Scenario loaded and validated')
        except (ValueError,KeyError,TypeError) as exc:st.error(str(exc))
    try:
        data=json.loads(content);simulate(data)
        valid=True;st.success('Valid process workload')
    except (ValueError,TypeError,KeyError) as exc:valid=False;st.error(f'Validation: {exc}')
    if valid:
        payload={'name':name,'processes':data,'algorithm':'FCFS','seed':42}
        st.download_button('Save Scenario',json.dumps(payload,indent=2),file_name='scenario.json',mime='application/json')
        if st.button('Execute Scenario',type='primary'):
            st.session_state.workload=data;st.session_state.scenario_name=name;st.session_state.result=simulate(data)
            st.success('Scenario executed; open Process Manager or Results to view output')
    if st.button('Load Example'):st.session_state.workload=[dict(p) for p in DEFAULT];st.rerun()
    if st.button('Clear Scenario'):st.session_state.workload=[];st.rerun()

def testing_page():
    init();st.header('Testing Center');st.caption('Runs deterministic expected-versus-actual baseline fixtures.')
    from engine.baselines import run_baselines
    if st.button('Run All Baseline Tests',type='primary'):st.session_state.test_rows=run_baselines(ROOT/'data')
    rows=st.session_state.test_rows
    if rows:
        cols=st.columns(3)
        for col,label,value in zip(cols,['Tests Passed','Tests Failed','Total Tests'],[sum(r['status']=='PASS' for r in rows),sum(r['status']=='FAIL' for r in rows),len(rows)]):col.metric(label,value)
        st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)
    st.caption('For the full unit, integration, invalid-input, boundary and replay suite, run: python -m unittest discover -s tests -v')

def results_page():
    init();st.header('Simulation Results');r=st.session_state.result
    if not r:st.info('Run a Process Manager or Scenario Builder simulation first.');return
    st.json(r['metrics']);chart(r['gantt'])
    st.dataframe(pd.DataFrame(r['processes']),hide_index=True)
    st.download_button('Export Summary',json.dumps(r,indent=2),file_name='simulation_results.json',mime='application/json')

def overview_page():
    init();st.header('System Overview')
    r=st.session_state.result
    cols=st.columns(4)
    for col,label,value in zip(cols,['Simulation Time','Run State','Active Scenario','Warnings'],[f"{r['metrics']['makespan']} ms" if r else '0 ms','Completed' if r else 'Ready',st.session_state.scenario_name,'0']):col.metric(label,value)
    st.info('Use Process Manager to execute a scheduling simulation, Scenario Builder to save/load workloads, or Testing Center to verify baseline fixtures.')
