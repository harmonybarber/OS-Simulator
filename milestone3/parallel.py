"""Deterministic multicore scheduling model; not a wall-clock benchmark."""
def simulate_parallel(tasks, cores=2, policy='Global Ready Queue'):
    if cores not in (1,2,4) or policy not in ('Global Ready Queue','Round-Robin Assignment','Least-Loaded Assignment'): raise ValueError('Invalid core count or policy')
    if not tasks or len(tasks)>200 or any(type(t.get('burst')) is not int or t['burst']<1 or type(t.get('arrival',0)) is not int or t.get('arrival',0)<0 for t in tasks): raise ValueError('Invalid tasks')
    if len({t['pid'] for t in tasks}) != len(tasks): raise ValueError('Duplicate task IDs')
    jobs = sorted(enumerate(tasks),key=lambda x:(x[1].get('arrival',0),x[0]))
    free = [0]*cores; gantt=[]; assignments=[[] for _ in range(cores)]
    for i, task in jobs:
        if policy == 'Round-Robin Assignment': core = i % cores
        elif policy == 'Least-Loaded Assignment': core = min(range(cores),key=lambda c:(free[c],c))
        else: core = min(range(cores),key=lambda c:(max(free[c],task.get('arrival',0)),c))
        start = max(free[core],task.get('arrival',0)); end=start+task['burst']; free[core]=end
        gantt.append({'core':core,'pid':task['pid'],'start':start,'end':end}); assignments[core].append(task['pid'])
    makespan=max(free); sequential=sum(t['burst'] for t in tasks)
    busy=[sum(s['end']-s['start'] for s in gantt if s['core']==c) for c in range(cores)]
    return {'gantt':sorted(gantt,key=lambda s:(s['start'],s['core'])), 'assignments':assignments,
            'sequential_time':sequential,'parallel_time':makespan,'speedup':sequential/makespan,
            'efficiency':sequential/makespan/cores*100,'per_core_utilization':[100*b/makespan for b in busy],
            'load_balance': min(busy)/max(busy) if max(busy) else 1.0}
