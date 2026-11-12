"""Thread primitives demonstration; deterministic unsafe interleaving model."""
import threading

def demonstrate(method='Mutex / Lock', workers=4, increments=100):
    if method not in ('Mutex / Lock','Semaphore','Barrier') or workers not in (1,2,4) or not 1 <= increments <= 10000: raise ValueError('Invalid synchronization settings')
    lock = threading.Lock(); semaphore = threading.Semaphore(1); barrier = threading.Barrier(workers)
    counter = [0]
    def worker():
        if method == 'Barrier': barrier.wait()
        for _ in range(increments):
            if method == 'Semaphore':
                with semaphore: counter[0] += 1
            else:
                with lock: counter[0] += 1
    threads = [threading.Thread(target=worker) for _ in range(workers)]
    for thread in threads: thread.start()
    for thread in threads: thread.join()
    return {'expected':workers*increments,'actual':counter[0],'pass':counter[0]==workers*increments,'method':method}

def race_demo(workers=4, increments=100):
    # Deliberate read-all/write-all interleaving to reproduce lost updates without timing dependence.
    return {'expected':workers*increments,'actual':increments,'lost':(workers-1)*increments,'mode':'Deterministic unsafe interleaving model'}

def detect_deadlock(edges):
    """Cycle detection in a single-instance wait-for graph."""
    graph={}; nodes=set()
    for a,b in edges: graph.setdefault(a,[]).append(b); nodes.update((a,b))
    seen=set(); active=set()
    def visit(v):
        if v in active:return True
        if v in seen:return False
        active.add(v)
        if any(visit(w) for w in graph.get(v,[])):return True
        active.remove(v);seen.add(v);return False
    return any(visit(v) for v in sorted(nodes) if v not in seen)
