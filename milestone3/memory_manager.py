from collections import deque, OrderedDict
from typing import List, Dict, Any

# Latency Model Assumptions (in nanoseconds)
HIT_LATENCY_NS = 10
FAULT_NO_EVICT_LATENCY_NS = 10_000
FAULT_EVICT_LATENCY_NS = 20_000


def parse_trace(trace_input: str) -> List[int]:
    """Converts comma- or space-separated page references into a list of integers."""
    if not trace_input or not trace_input.strip():
        return []
    cleaned = trace_input.replace(",", " ").split()
    return [int(item) for item in cleaned]


def simulate_fifo(reference_trace: List[int], capacity: int) -> Dict[str, Any]:
    """Simulates First-In, First-Out (FIFO) page replacement."""
    if capacity <= 0:
        raise ValueError("Frame capacity must be greater than 0.")

    frames = deque()
    steps = []
    hits = 0
    faults = 0
    evictions = 0
    total_latency_ns = 0

    for step_idx, page in enumerate(reference_trace, start=1):
        evicted_page = None
        if page in frames:
            status = "Hit"
            hits += 1
            total_latency_ns += HIT_LATENCY_NS
        else:
            status = "Page Fault"
            faults += 1
            if len(frames) >= capacity:
                evicted_page = frames.popleft()
                evictions += 1
                total_latency_ns += FAULT_EVICT_LATENCY_NS
            else:
                total_latency_ns += FAULT_NO_EVICT_LATENCY_NS
            frames.append(page)

        steps.append({
            "Step": step_idx,
            "Page": page,
            "Frames": " | ".join(str(f) for f in frames),
            "Result": status,
            "Evicted": evicted_page if evicted_page is not None else "",
            "Latency (ns)": HIT_LATENCY_NS if status == "Hit" else (
                FAULT_EVICT_LATENCY_NS if evicted_page is not None else FAULT_NO_EVICT_LATENCY_NS
            )
        })

    total_refs = len(reference_trace)
    fault_rate = (faults / total_refs * 100.0) if total_refs > 0 else 0.0

    return {
        "algorithm": "FIFO",
        "capacity": capacity,
        "total_references": total_refs,
        "hits": hits,
        "faults": faults,
        "fault_rate": round(fault_rate, 2),
        "evictions": evictions,
        "simulated_latency_ns": total_latency_ns,
        "steps": steps
    }


def simulate_lru(reference_trace: List[int], capacity: int) -> Dict[str, Any]:
    """Simulates Least Recently Used (LRU) page replacement."""
    if capacity <= 0:
        raise ValueError("Frame capacity must be greater than 0.")

    frames = OrderedDict()
    steps = []
    hits = 0
    faults = 0
    evictions = 0
    total_latency_ns = 0

    for step_idx, page in enumerate(reference_trace, start=1):
        evicted_page = None
        if page in frames:
            status = "Hit"
            hits += 1
            frames.move_to_end(page)
            total_latency_ns += HIT_LATENCY_NS
        else:
            status = "Page Fault"
            faults += 1
            if len(frames) >= capacity:
                evicted_page, _ = frames.popitem(last=False)
                evictions += 1
                total_latency_ns += FAULT_EVICT_LATENCY_NS
            else:
                total_latency_ns += FAULT_NO_EVICT_LATENCY_NS
            frames[page] = True

        steps.append({
            "Step": step_idx,
            "Page": page,
            "Frames": " | ".join(str(f) for f in frames.keys()),
            "Result": status,
            "Evicted": evicted_page if evicted_page is not None else "",
            "Latency (ns)": HIT_LATENCY_NS if status == "Hit" else (
                FAULT_EVICT_LATENCY_NS if evicted_page is not None else FAULT_NO_EVICT_LATENCY_NS
            )
        })

    total_refs = len(reference_trace)
    fault_rate = (faults / total_refs * 100.0) if total_refs > 0 else 0.0

    return {
        "algorithm": "LRU",
        "capacity": capacity,
        "total_references": total_refs,
        "hits": hits,
        "faults": faults,
        "fault_rate": round(fault_rate, 2),
        "evictions": evictions,
        "simulated_latency_ns": total_latency_ns,
        "steps": steps
    }


def compare_algorithms(reference_trace: List[int], capacity: int) -> Dict[str, Any]:
    """Run both FIFO and LRU on the exact same page trace and frame capacity."""
    return {
        "fifo": simulate_fifo(reference_trace, capacity),
        "lru": simulate_lru(reference_trace, capacity),
    }