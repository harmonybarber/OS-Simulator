"""Deterministic integer-millisecond CPU scheduling engine with memory & file hooks.

Boundary order: arrivals, I/O completions, quantum expiry, preemption, dispatch.
Ties: FIFO ready-entry order, then input order. Lower priority number is better.
"""
from dataclasses import dataclass, asdict, field
from typing import Optional, Tuple, Dict, Any, List

ALGORITHMS = ("FCFS", "SJF", "SRTF", "Round Robin", "Priority with Aging")


@dataclass(frozen=True)
class Process:
    pid: str
    arrival: int
    burst: int
    priority: int = 3
    io_start: Optional[int] = None
    io_duration: int = 0
    memory_pages: Tuple[int, ...] = field(default_factory=tuple)
    file_requests: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)


def validate(processes, algorithm="FCFS", quantum=4, aging_interval=5, context_cost=0):
    if algorithm not in ALGORITHMS:
        raise ValueError("Unknown scheduling algorithm")
    if type(quantum) is not int or quantum < 1:
        raise ValueError("Quantum must be a positive integer")
    if type(aging_interval) is not int or aging_interval < 1:
        raise ValueError("Aging interval must be positive")
    if type(context_cost) is not int or context_cost < 0:
        raise ValueError("Context cost must be a nonnegative integer")
    if not processes or len(processes) > 200:
        raise ValueError("Process count must be between 1 and 200")
    seen = set()
    for p in processes:
        if not isinstance(p.pid, str) or not p.pid.strip() or p.pid in seen:
            raise ValueError("Process IDs must be unique and nonempty")
        seen.add(p.pid)
        for name in ("arrival", "burst", "priority", "io_duration"):
            value = getattr(p, name)
            minimum = 0 if name in ("arrival", "io_duration") else 1
            if type(value) is not int or value < minimum:
                raise ValueError(f"{p.pid}: invalid {name}")
        if p.io_start is None:
            if p.io_duration:
                raise ValueError(f"{p.pid}: I/O duration without I/O start")
        elif (
            type(p.io_start) is not int
            or not 1 <= p.io_start < p.burst
            or p.io_duration < 1
        ):
            raise ValueError(f"{p.pid}: invalid I/O configuration")
        for req in p.file_requests:
            at_tick = req.get("at_tick")
            if type(at_tick) is not int or not 1 <= at_tick <= p.burst:
                raise ValueError(f"{p.pid}: file request at_tick must be within 1..burst")
        if p.arrival + p.burst + p.io_duration > 100000:
            raise ValueError("Simulation exceeds 100000 ms")


def _normalize_process(p) -> Process:
    if isinstance(p, Process):
        return p
    data = dict(p)
    if "memory_pages" in data and isinstance(data["memory_pages"], list):
        data["memory_pages"] = tuple(data["memory_pages"])
    if "file_requests" in data and isinstance(data["file_requests"], list):
        data["file_requests"] = tuple(data["file_requests"])
    return Process(**data)


def _page_for_tick(p: Process, tick_index: int) -> int:
    """Return the virtual page referenced by process `p` on its `tick_index`-th CPU tick."""
    if p.memory_pages:
        return int(p.memory_pages[tick_index % len(p.memory_pages)])
    pid_base = (sum(ord(ch) for ch in p.pid) % 8) * 10
    return pid_base + (tick_index // 2)


def simulate(
    processes,
    algorithm="FCFS",
    quantum=4,
    aging_interval=5,
    context_cost=0,
    filesystem=None,
):
    processes = [_normalize_process(p) for p in processes]
    validate(processes, algorithm, quantum, aging_interval, context_cost)
    info = {p.pid: p for p in processes}
    remaining = {p.pid: p.burst for p in processes}
    consumed = {p.pid: 0 for p in processes}
    states = {p.pid: "New" for p in processes}
    first, completion, ready_since = {}, {}, {}
    ready_wait = {p.pid: 0 for p in processes}
    ready, gantt, events, snapshots = [], [], [], []
    memory_references: List[Dict[str, Any]] = []
    file_events: List[Dict[str, Any]] = []

    pending_file_reqs: Dict[Tuple[str, int], List[Dict[str, Any]]] = {}
    for p in processes:
        for req in p.file_requests:
            pending_file_reqs.setdefault((p.pid, req["at_tick"]), []).append(req)

    io_done, io_used = {}, set()
    t, running, q_used, previous, switches, busy = 0, None, 0, None, 0, 0
    switching_until = None
    switch_paid = False

    def event(pid, state, detail: Optional[str] = None):
        states[pid] = state
        entry = {"time": t, "pid": pid, "state": state}
        if detail:
            entry["detail"] = detail
        events.append(entry)

    def enqueue(pid, detail: Optional[str] = None):
        event(pid, "Ready", detail=detail)
        ready_since[pid] = t
        ready.append(pid)

    def segment(pid):
        if gantt and gantt[-1]["pid"] == pid and gantt[-1]["end"] == t:
            gantt[-1]["end"] += 1
        else:
            gantt.append({"pid": pid, "start": t, "end": t + 1})

    def snapshot(label):
        snapshots.append({
            "time": t,
            "running": label,
            "ready": list(ready),
            "states": dict(states),
        })

    def rank(pid):
        p = info[pid]
        if algorithm == "SJF":
            return (p.burst, ready.index(pid))
        if algorithm == "SRTF":
            return (remaining[pid], ready.index(pid))
        if algorithm == "Priority with Aging":
            effective = max(0, p.priority - (t - ready_since[pid]) // aging_interval)
            return (effective, ready.index(pid))
        return (ready.index(pid),)

    extra_io = sum(
        req.get("io_duration", 1)
        for p in processes
        for req in p.file_requests
    )
    limit = (
        max(p.arrival for p in processes)
        + sum(p.burst + p.io_duration for p in processes)
        + extra_io
        + context_cost * (sum(p.burst for p in processes) + len(processes))
        + 1000
    )

    while len(completion) < len(processes):
        if t > limit:
            raise RuntimeError("Simulation exceeded safety time limit")

        for p in processes:
            if p.arrival == t:
                enqueue(p.pid, detail="Arrived")
        for p in processes:
            if io_done.get(p.pid) == t:
                del io_done[p.pid]
                enqueue(p.pid, detail="I/O Complete")

        if running is not None and algorithm == "Round Robin" and q_used >= quantum:
            enqueue(running, detail="Quantum Expired")
            running, q_used = None, 0
        if running is not None and ready and algorithm in ("SRTF", "Priority with Aging"):
            best = min(ready, key=rank)
            if algorithm == "SRTF":
                preempt = remaining[best] < remaining[running]
            else:
                preempt = rank(best)[0] < info[running].priority
            if preempt:
                enqueue(running, detail="Preempted")
                running, q_used = None, 0

        if switching_until is not None:
            if t < switching_until:
                segment("CS")
                snapshot("CS")
                t += 1
                continue
            switching_until = None
            switch_paid = True

        if running is None and ready:
            selected = ready[0] if algorithm in ("FCFS", "Round Robin") else min(ready, key=rank)
            if previous is not None and selected != previous and not switch_paid:
                switches += 1
                if context_cost:
                    switching_until = t + context_cost
                    segment("CS")
                    snapshot("CS")
                    t += 1
                    continue
            switch_paid = False
            ready.remove(selected)
            ready_wait[selected] += t - ready_since[selected]
            running, q_used = selected, 0
            if selected not in first:
                first[selected] = t
            event(selected, "Running")

        if running is None:
            segment("Idle")
            snapshot("Idle")
            previous = None
            switch_paid = False
            t += 1
            continue

        pid = running
        page = _page_for_tick(info[pid], consumed[pid])
        memory_references.append({
            "time": t,
            "pid": pid,
            "tick": consumed[pid] + 1,
            "page": page,
        })

        snapshot(pid)
        segment(pid)
        busy += 1
        remaining[pid] -= 1
        consumed[pid] += 1
        q_used += 1
        t += 1
        previous = pid

        block_duration = 0
        if (pid, consumed[pid]) in pending_file_reqs:
            for req in pending_file_reqs.pop((pid, consumed[pid])):
                cmd = req["command"]
                path = req["path"]
                content = req.get("content", "")
                io_dur = int(req.get("io_duration", 1))
                try:
                    if filesystem is not None:
                        fs_out = filesystem.execute(cmd, path, content=content, pid=pid)
                    else:
                        fs_out = "Simulated (no filesystem attached)"
                    file_events.append({
                        "time": t,
                        "pid": pid,
                        "command": cmd,
                        "path": path,
                        "status": "AUTHORIZED",
                        "result": fs_out,
                    })
                    if remaining[pid] > 0 and io_dur > 0:
                        block_duration = max(block_duration, io_dur)
                except PermissionError as exc:
                    file_events.append({
                        "time": t,
                        "pid": pid,
                        "command": cmd,
                        "path": path,
                        "status": "DENIED",
                        "result": str(exc),
                    })
                except ValueError as exc:
                    file_events.append({
                        "time": t,
                        "pid": pid,
                        "command": cmd,
                        "path": path,
                        "status": "ERROR",
                        "result": str(exc),
                    })

        if remaining[pid] == 0:
            completion[pid] = t
            event(pid, "Terminated")
            running = None
        elif block_duration > 0:
            io_done[pid] = t + block_duration
            event(pid, "Blocked", detail="File I/O Wait")
            running = None
        elif (
            info[pid].io_start is not None
            and pid not in io_used
            and consumed[pid] == info[pid].io_start
        ):
            io_used.add(pid)
            io_done[pid] = t + info[pid].io_duration
            event(pid, "Blocked", detail="Device I/O Wait")
            running = None

    rows = []
    for p in processes:
        turnaround = completion[p.pid] - p.arrival
        rows.append({
            "pid": p.pid,
            "arrival": p.arrival,
            "burst": p.burst,
            "priority": p.priority,
            "waiting": ready_wait[p.pid],
            "response": first[p.pid] - p.arrival,
            "turnaround": turnaround,
            "completion": completion[p.pid],
            "state": "Terminated",
        })
    metrics = {
        "makespan": t,
        "cpu_busy": busy,
        "cpu_utilization": 100 * busy / t,
        "throughput": len(processes) / t,
        "context_switches": switches,
        "avg_waiting": sum(r["waiting"] for r in rows) / len(rows),
        "avg_response": sum(r["response"] for r in rows) / len(rows),
        "avg_turnaround": sum(r["turnaround"] for r in rows) / len(rows),
    }
    return {
        "algorithm": algorithm,
        "processes": rows,
        "metrics": metrics,
        "gantt": gantt,
        "events": events,
        "snapshots": snapshots,
        "memory_references": memory_references,
        "file_events": file_events,
        "config": [asdict(p) for p in processes],
    }
