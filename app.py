
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="OS Simulator",
    page_icon="💻",
    layout="wide",
)

# ---------------- SAMPLE DATA ----------------
DEFAULT_PROCESSES = [
    {"PID": "P1", "Arrival": 0, "Burst": 8, "Priority": 3},
    {"PID": "P2", "Arrival": 1, "Burst": 4, "Priority": 1},
    {"PID": "P3", "Arrival": 2, "Burst": 9, "Priority": 4},
    {"PID": "P4", "Arrival": 3, "Burst": 5, "Priority": 2},
]


def schedule_processes(processes, policy, quantum=4):
    """Return a simple CPU timeline and per-process metrics."""
    jobs = [
        {
            **p,
            "remaining": int(p["Burst"]),
            "start": None,
            "completion": None,
        }
        for p in processes
    ]
    if not jobs or any(
        p["Arrival"] < 0 or p["Burst"] <= 0 for p in jobs
    ):
        raise ValueError("Arrival must be >= 0 and burst must be > 0.")

    clock = 0
    timeline = []
    ready_queue = []
    finished = []
    last_pid = None

    while len(finished) < len(jobs):
        available = [
            p for p in jobs
            if p["Arrival"] <= clock
            and p["remaining"] > 0
            and p not in ready_queue
        ]

        # For non-preemptive algorithms, choose from available jobs.
        if policy == "Round Robin":
            for p in sorted(available, key=lambda x: (x["Arrival"], x["PID"])):
                ready_queue.append(p)
            if not ready_queue:
                next_arrival = min(
                    p["Arrival"] for p in jobs if p["remaining"] > 0
                )
                if next_arrival > clock:
                    timeline.append({"Start": clock, "End": next_arrival, "Process": "Idle"})
                    clock = next_arrival
                continue
            current = ready_queue.pop(0)
            run_for = min(quantum, current["remaining"])
        else:
            candidates = [
                p for p in jobs
                if p["Arrival"] <= clock and p["remaining"] > 0
            ]
            if not candidates:
                next_arrival = min(
                    p["Arrival"] for p in jobs if p["remaining"] > 0
                )
                if next_arrival > clock:
                    timeline.append({"Start": clock, "End": next_arrival, "Process": "Idle"})
                    clock = next_arrival
                continue

            if policy == "FCFS":
                current = min(candidates, key=lambda p: (p["Arrival"], p["PID"]))
            elif policy == "SJF":
                current = min(candidates, key=lambda p: (p["Burst"], p["Arrival"], p["PID"]))
            elif policy == "Priority":
                current = min(candidates, key=lambda p: (p["Priority"], p["Arrival"], p["PID"]))
            else:  # SRTF: choose the shortest remaining time each time unit
                current = min(candidates, key=lambda p: (p["remaining"], p["Arrival"], p["PID"]))
            run_for = 1 if policy == "SRTF" else current["remaining"]

        if current["start"] is None:
            current["start"] = clock

        start = clock
        current["remaining"] -= run_for
        clock += run_for
        timeline.append({"Start": start, "End": clock, "Process": current["PID"]})

        if current["remaining"] == 0:
            current["completion"] = clock
            finished.append(current)

        if policy == "Round Robin" and current["remaining"] > 0:
            # Add processes that arrived while this time slice ran.
            for p in sorted(jobs, key=lambda x: (x["Arrival"], x["PID"])):
                if (
                    p["Arrival"] <= clock and p["remaining"] > 0
                    and p not in ready_queue and p is not current
                ):
                    ready_queue.append(p)
            ready_queue.append(current)

        last_pid = current["PID"]

    results = []
    for p in jobs:
        turnaround = p["completion"] - p["Arrival"]
        waiting = turnaround - p["Burst"]
        results.append({
            "PID": p["PID"],
            "Arrival": p["Arrival"],
            "Burst": p["Burst"],
            "Priority": p["Priority"],
            "Start": p["start"],
            "Completion": p["completion"],
            "Turnaround": turnaround,
            "Waiting": waiting,
        })

    return pd.DataFrame(timeline), pd.DataFrame(results)


def replace_pages(reference_string, frame_count, policy):
    """Simulate FIFO or LRU page replacement."""
    frames = []
    history = []
    faults = 0
    queue = []
    last_used = {}

    for time, page in enumerate(reference_string):
        fault = page not in frames
        evicted = "-"

        if fault:
            faults += 1
            if len(frames) < frame_count:
                frames.append(page)
                queue.append(page)
            else:
                if policy == "FIFO":
                    victim = queue.pop(0)
                else:
                    victim = min(frames, key=lambda item: last_used[item])
                evicted = str(victim)
                frames[frames.index(victim)] = page
                queue.append(page)

        last_used[page] = time
        history.append({
            "Reference #": time + 1,
            "Page": page,
            "Frames": ", ".join(map(str, frames)),
            "Result": "Fault" if fault else "Hit",
            "Evicted": evicted,
        })

    return pd.DataFrame(history), faults


# ---------------- SIDEBAR ----------------
st.sidebar.title("💻 OS Simulator")
st.sidebar.caption("Operating System Simulation Dashboard")
page = st.sidebar.radio(
    "Navigate",
    ["Overview", "Process Manager", "Memory Manager"],
)
st.sidebar.divider()
st.sidebar.caption("Demo build · Sample workloads")

# ---------------- OVERVIEW ----------------
if page == "Overview":
    st.title("Operating System Simulator")
    st.write("Monitor and explore simulated operating-system managers.")
    st.info(
        "Demonstration mode: results are generated from sample inputs. "
        "This is not a real operating system and does not change host files."
    )

    a, b, c, d = st.columns(4)
    a.metric("Managers shown", "2 / 6")
    b.metric("Sample processes", len(DEFAULT_PROCESSES))
    c.metric("Memory frames", "3")
    d.metric("Simulation clock", "Ready")

    st.subheader("Manager status")
    status = pd.DataFrame([
        {"Manager": "Process Manager", "Status": "Demo available", "Purpose": "CPU scheduling"},
        {"Manager": "Memory Manager", "Status": "Demo available", "Purpose": "Page replacement"},
        {"Manager": "File Manager", "Status": "Not implemented", "Purpose": "File-system simulation"},
        {"Manager": "Security Manager", "Status": "Not implemented", "Purpose": "Roles and permissions"},
        {"Manager": "Device Manager", "Status": "Not implemented", "Purpose": "Device queues"},
        {"Manager": "Network Manager", "Status": "Not implemented", "Purpose": "Packets and routing"},
    ])
    st.dataframe(status, use_container_width=True, hide_index=True)

    st.subheader("How to use the dashboard")
    st.markdown(
        "- Select **Process Manager** to compare CPU scheduling policies.\n"
        "- Select **Memory Manager** to test FIFO or LRU page replacement.\n"
        "- The other managers are listed as future work, not completed features."
    )

# ---------------- PROCESS MANAGER ----------------
elif page == "Process Manager":
    st.title("Process Manager")
    st.write("Explore CPU scheduling using a small, editable sample workload.")

    edited = st.data_editor(
        pd.DataFrame(DEFAULT_PROCESSES),
        num_rows="dynamic",
        use_container_width=True,
        key="process_editor",
    )

    policy = st.selectbox(
        "Scheduling policy",
        ["FCFS", "SJF", "SRTF", "Round Robin", "Priority"],
    )
    quantum = 4
    if policy == "Round Robin":
        quantum = st.number_input("Time quantum", min_value=1, value=4, step=1)

    if st.button("Run scheduling simulation", type="primary"):
        try:
            records = edited.to_dict("records")
            clean = []
            for row in records:
                clean.append({
                    "PID": str(row["PID"]),
                    "Arrival": int(row["Arrival"]),
                    "Burst": int(row["Burst"]),
                    "Priority": int(row["Priority"]),
                })
            if not clean:
                raise ValueError("Add at least one process.")
            if len({p["PID"] for p in clean}) != len(clean):
                raise ValueError("Each process must have a unique PID.")

            timeline, metrics = schedule_processes(clean, policy, quantum)
            st.session_state["timeline"] = timeline
            st.session_state["process_metrics"] = metrics
            st.session_state["process_policy"] = policy
        except (ValueError, TypeError, KeyError) as error:
            st.error(f"Unable to run simulation: {error}")

    if "timeline" in st.session_state:
        st.subheader(f"CPU timeline — {st.session_state['process_policy']}")
        timeline = st.session_state["timeline"]
        st.dataframe(timeline, use_container_width=True, hide_index=True)
        st.caption("Each row represents a CPU execution interval; time units are simulated units.")

        metrics = st.session_state["process_metrics"]
        st.subheader("Process performance metrics")
        st.dataframe(metrics, use_container_width=True, hide_index=True)
        st.metric("Average waiting time", f"{metrics['Waiting'].mean():.2f} time units")
        st.metric("Average turnaround time", f"{metrics['Turnaround'].mean():.2f} time units")

# ---------------- MEMORY MANAGER ----------------
else:
    st.title("Memory Manager")
    st.write("Explore how page replacement changes simulated memory frames.")

    references_text = st.text_input(
        "Page-reference string (separate page numbers with commas)",
        value="1, 2, 3, 1, 4, 2, 5, 1, 2, 3, 4, 5",
    )
    frame_count = st.number_input("Number of frames", min_value=1, max_value=10, value=3)
    policy = st.selectbox("Page-replacement policy", ["FIFO", "LRU"])

    if st.button("Run memory simulation", type="primary"):
        try:
            references = [
                int(item.strip())
                for item in references_text.split(",")
                if item.strip()
            ]
            if not references:
                raise ValueError("Enter at least one page number.")
            if any(page < 0 for page in references):
                raise ValueError("Page numbers must be non-negative.")

            history, faults = replace_pages(references, int(frame_count), policy)
            st.session_state["memory_history"] = history
            st.session_state["memory_faults"] = faults
            st.session_state["memory_policy"] = policy
        except ValueError as error:
            st.error(f"Unable to run simulation: {error}")

    if "memory_history" in st.session_state:
        history = st.session_state["memory_history"]
        faults = st.session_state["memory_faults"]
        st.subheader(f"Memory access history — {st.session_state['memory_policy']}")
        st.dataframe(history, use_container_width=True, hide_index=True)
        hits = len(history) - faults
        a, b, c = st.columns(3)
        a.metric("Page references", len(history))
        b.metric("Page faults", faults)
        c.metric("Page hits", hits)
        st.caption("A page fault occurs when the requested page is not currently in a frame.")
