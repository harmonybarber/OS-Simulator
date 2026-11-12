
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from collections import deque
import io
import json
from datetime import datetime, timezone

from engine.memory_manager import (
    parse_trace,
    simulate_fifo,
    simulate_lru,
    compare_algorithms,
    HIT_LATENCY_NS,
    FAULT_NO_EVICT_LATENCY_NS,
    FAULT_EVICT_LATENCY_NS,
)
# ==================================================
# PAGE SETUP
# ==================================================





# ==================================================
# DEFAULT DATA
# ==================================================

DEFAULT_PROCESSES = pd.DataFrame({
    "Process": ["P1", "P2", "P3", "P4"],
    "Arrival": [0, 1, 2, 3],
    "Burst": [8, 4, 9, 5],
    "Priority": [3, 1, 4, 2],
})


# ==================================================
# CPU SCHEDULING
# ==================================================

def schedule_processes(processes, policy, quantum=4):
    """Return CPU intervals and process performance metrics."""

    jobs = []

    for index, row in processes.reset_index(drop=True).iterrows():
        jobs.append({
            "index": index,
            "Process": str(row["Process"]),
            "Arrival": int(row["Arrival"]),
            "Burst": int(row["Burst"]),
            "Priority": int(row["Priority"]),
            "Remaining": int(row["Burst"]),
        })

    if not jobs:
        return [], pd.DataFrame()

    timeline = []
    completion = {}
    current_time = 0

    def add_interval(start, end, process_name):
        if end <= start:
            return

        # Combine consecutive intervals belonging to the same process.
        if (
            timeline
            and timeline[-1]["Process"] == process_name
            and timeline[-1]["End"] == start
        ):
            timeline[-1]["End"] = end
        else:
            timeline.append({
                "Start": start,
                "End": end,
                "Process": process_name,
            })

    # ------------------------------------------------
    # FCFS, SJF, AND NON-PREEMPTIVE PRIORITY
    # ------------------------------------------------

    if policy in ("FCFS", "SJF", "Priority"):
        unfinished = jobs.copy()

        while unfinished:
            ready = [
                job for job in unfinished
                if job["Arrival"] <= current_time
            ]

            if not ready:
                next_arrival = min(
                    job["Arrival"] for job in unfinished
                )

                add_interval(
                    current_time, next_arrival, "Idle"
                )
                current_time = next_arrival
                continue

            if policy == "FCFS":
                chosen = min(
                    ready,
                    key=lambda job: (
                        job["Arrival"], job["index"]
                    ),
                )
            elif policy == "SJF":
                chosen = min(
                    ready,
                    key=lambda job: (
                        job["Burst"],
                        job["Arrival"],
                        job["index"],
                    ),
                )
            else:
                chosen = min(
                    ready,
                    key=lambda job: (
                        job["Priority"],
                        job["Arrival"],
                        job["index"],
                    ),
                )

            start = current_time
            current_time += chosen["Remaining"]

            add_interval(
                start, current_time, chosen["Process"]
            )

            completion[chosen["Process"]] = current_time
            chosen["Remaining"] = 0
            unfinished.remove(chosen)

    # ------------------------------------------------
    # SRTF: SHORTEST REMAINING TIME FIRST
    # ------------------------------------------------

    elif policy == "SRTF":
        while any(job["Remaining"] > 0 for job in jobs):
            ready = [
                job for job in jobs
                if (
                    job["Arrival"] <= current_time
                    and job["Remaining"] > 0
                )
            ]

            if not ready:
                next_arrival = min(
                    job["Arrival"]
                    for job in jobs
                    if (
                        job["Remaining"] > 0
                        and job["Arrival"] > current_time
                    )
                )

                add_interval(
                    current_time, next_arrival, "Idle"
                )
                current_time = next_arrival
                continue

            chosen = min(
                ready,
                key=lambda job: (
                    job["Remaining"],
                    job["Arrival"],
                    job["index"],
                ),
            )

            add_interval(
                current_time,
                current_time + 1,
                chosen["Process"],
            )

            chosen["Remaining"] -= 1
            current_time += 1

            if chosen["Remaining"] == 0:
                completion[chosen["Process"]] = current_time

    # ------------------------------------------------
    # ROUND ROBIN
    # ------------------------------------------------

    elif policy == "Round Robin":
        ready_queue = deque()
        next_index = 0

        while (
            next_index < len(jobs)
            or ready_queue
        ):
            if not ready_queue:
                next_arrival = jobs[next_index]["Arrival"]

                if current_time < next_arrival:
                    add_interval(
                        current_time, next_arrival, "Idle"
                    )
                    current_time = next_arrival

            while (
                next_index < len(jobs)
                and jobs[next_index]["Arrival"] <= current_time
            ):
                ready_queue.append(jobs[next_index])
                next_index += 1

            if not ready_queue:
                continue

            chosen = ready_queue.popleft()
            duration = min(quantum, chosen["Remaining"])

            start = current_time
            current_time += duration

            add_interval(
                start, current_time, chosen["Process"]
            )

            chosen["Remaining"] -= duration

            # Add newly arrived processes before re-queueing
            # the process whose quantum has just finished.
            while (
                next_index < len(jobs)
                and jobs[next_index]["Arrival"] <= current_time
            ):
                ready_queue.append(jobs[next_index])
                next_index += 1

            if chosen["Remaining"] > 0:
                ready_queue.append(chosen)
            else:
                completion[chosen["Process"]] = current_time

    # ------------------------------------------------
    # PROCESS METRICS
    # ------------------------------------------------

    metric_rows = []

    for job in jobs:
        finish = completion[job["Process"]]
        turnaround = finish - job["Arrival"]
        waiting = turnaround - job["Burst"]

        metric_rows.append({
            "Process": job["Process"],
            "Arrival": job["Arrival"],
            "Burst": job["Burst"],
            "Priority": job["Priority"],
            "Completion": finish,
            "Turnaround": turnaround,
            "Waiting": waiting,
        })

    return timeline, pd.DataFrame(metric_rows)


# ==================================================
# CPU GANTT CHART
# ==================================================

def display_gantt_chart(timeline):
    st.subheader("CPU Gantt Chart")

    if not timeline:
        st.info("Run the scheduler to generate a Gantt chart.")
        return

    colors = [
        "#A8C7FA",
        "#A8DDB5",
        "#F6C99A",
        "#D6B9F0",
        "#F2A7B5",
        "#9EDCE0",
        "#F4E18A",
        "#C7D0DB",
    ]

    process_names = list(dict.fromkeys(
        item["Process"]
        for item in timeline
        if item["Process"] != "Idle"
    ))

    color_map = {
        name: colors[i % len(colors)]
        for i, name in enumerate(process_names)
    }
    color_map["Idle"] = "#D0D0D0"

    fig = go.Figure()

    # All intervals share one CPU lane. The base value sets
    # each block's starting time on the horizontal axis.
    for interval in timeline:
        name = interval["Process"]
        start = interval["Start"]
        end = interval["End"]

        fig.add_trace(go.Bar(
            x=[end - start],
            y=["CPU"],
            base=[start],
            orientation="h",
            marker=dict(
                color=color_map.get(name, "#A8C7FA"),
                line=dict(color="white", width=2),
            ),
            name=name,
            text=[name],
            textposition="inside",
            insidetextanchor="middle",
            customdata=[[start, end, end - start]],
            hovertemplate=(
                "<b>%{text}</b>"
                "<br>Start: %{customdata[0]}"
                "<br>End: %{customdata[1]}"
                "<br>Duration: %{customdata[2]}"
                "<extra></extra>"
            ),
            showlegend=False,
        ))

    fig.update_layout(
        title="CPU Execution Timeline",
        xaxis_title="Simulation Time",
        yaxis_title="",
        barmode="overlay",
        height=220,
        margin=dict(l=25, r=25, t=55, b=45),
        showlegend=False,
    )

    fig.update_xaxes(
        type="linear",
        range=[
            0,
            max(item["End"] for item in timeline) + 0.5,
        ],
        dtick=1,
        showgrid=True,
        zeroline=True,
    )

    fig.update_yaxes(
        showticklabels=True,
        showgrid=False,
        fixedrange=True,
    )

    st.plotly_chart(fig, use_container_width=True)

    st.caption(
        "Each colored block represents a CPU execution interval. "
        "Hover over a block to see its start time, end time, "
        "and duration. Gray blocks represent CPU idle time."
    )


# ==================================================
# MEMORY PAGE REPLACEMENT
# ==================================================

def replace_pages(reference_string, frame_count, policy):
    """Return step-by-step FIFO/LRU trace and fault/hit counts."""
    if frame_count < 1 or policy not in ("FIFO", "LRU"):
        raise ValueError("Invalid frame count or policy")
    frames = [None] * frame_count
    fifo_queue = deque()
    last_used = {}
    history = []
    faults = hits = 0
    for step, page in enumerate(reference_string):
        evicted = None
        if page in frames:
            hits += 1
            result = "Hit"
        else:
            faults += 1
            result = "Page Fault"
            if None in frames:
                slot = frames.index(None)
            elif policy == "FIFO":
                evicted = fifo_queue.popleft()
                slot = frames.index(evicted)
            else:
                slot = min(range(frame_count), key=lambda i: last_used[frames[i]])
                evicted = frames[slot]
            frames[slot] = page
            if policy == "FIFO":
                fifo_queue.append(page)
        last_used[page] = step
        history.append({
            "Step": step + 1, "Page": page,
            "Frames": " | ".join("-" if v is None else str(v) for v in frames),
            "Result": result, "Evicted": "" if evicted is None else evicted,
            "Latency (units)": 5 if result == "Page Fault" else 1,
        })
    return pd.DataFrame(history), faults, hits


def init_file_system():
    return {"type": "dir", "children": {}}


def fs_node(root, path):
    if not path.startswith("/"):
        raise ValueError("Use absolute paths beginning with /")
    node = root
    for name in [x for x in path.split("/") if x]:
        if node["type"] != "dir" or name not in node["children"]:
            raise ValueError(f"Path not found: {path}")
        node = node["children"][name]
    return node


def fs_parent(root, path):
    parts = [x for x in path.split("/") if x]
    if not path.startswith("/") or not parts or any(x in (".", "..") for x in parts):
        raise ValueError("Provide an absolute non-root path without . or ..")
    parent = fs_node(root, "/" + "/".join(parts[:-1]))
    if parent["type"] != "dir":
        raise ValueError("Parent is not a directory")
    return parent, parts[-1]


def fs_command(root, command, path, content=""):
    """Educational in-memory file system. No host disk operations."""
    if command == "ls":
        node = fs_node(root, path)
        if node["type"] != "dir":
            raise ValueError("Not a directory")
        return ", ".join(sorted(node["children"])) or "(empty directory)"
    if command == "cat":
        node = fs_node(root, path)
        if node["type"] != "file":
            raise ValueError("Not a file")
        return node["content"]
    parent, name = fs_parent(root, path)
    exists = name in parent["children"]
    if command in ("mkdir", "touch"):
        if exists:
            raise ValueError("Path already exists")
        parent["children"][name] = ({"type": "dir", "children": {}} if command == "mkdir"
                                    else {"type": "file", "content": ""})
    elif command == "write":
        if not exists or parent["children"][name]["type"] != "file":
            raise ValueError("File not found")
        parent["children"][name]["content"] = content
    elif command == "rm":
        if not exists or parent["children"][name]["type"] != "file":
            raise ValueError("File not found")
        del parent["children"][name]
    elif command == "rmdir":
        if not exists or parent["children"][name]["type"] != "dir":
            raise ValueError("Directory not found")
        if parent["children"][name]["children"]:
            raise ValueError("Directory is not empty")
        del parent["children"][name]
    else:
        raise ValueError("Unknown command")
    return f"{command} {path}: OK"


def fs_tree(node, prefix="/"):
    rows = [{"Path": prefix, "Type": node["type"],
             "Size": len(node.get("content", "")) if node["type"] == "file" else ""}]
    if node["type"] == "dir":
        for name, child in sorted(node["children"].items()):
            rows.extend(fs_tree(child, prefix.rstrip("/") + "/" + name))
    return rows


def run_dashboard_tests():
    results = []
    def check(name, fn):
        try:
            fn()
            results.append({"Test": name, "Status": "PASS", "Details": ""})
        except Exception as exc:
            results.append({"Test": name, "Status": "FAIL", "Details": str(exc)})
    def memory_check():
        for policy in ("FIFO", "LRU"):
            trace, faults, hits = replace_pages([1, 2, 1, 3, 1], 2, policy)
            assert (faults, hits) == ((4, 1) if policy == "FIFO" else (3, 2))
            assert len(trace) == 5
    def file_check():
        root = init_file_system()
        fs_command(root, "mkdir", "/docs")
        fs_command(root, "touch", "/docs/note.txt")
        fs_command(root, "write", "/docs/note.txt", "hello")
        assert fs_command(root, "cat", "/docs/note.txt") == "hello"
        try:
            fs_command(root, "rmdir", "/docs")
            raise AssertionError("Nonempty directory should be rejected")
        except ValueError:
            pass
    check("FIFO and LRU reference trace", memory_check)
    check("File create, write, read and error handling", file_check)
    return pd.DataFrame(results)


def log_event(message):
    st.session_state.setdefault("activity_log", []).append(
        f"{datetime.now(timezone.utc).isoformat()} | {message}")


def export_buttons(df, basename, key):
    st.download_button("Download CSV", df.to_csv(index=False).encode("utf-8"),
                       file_name=f"{basename}.csv", mime="text/csv", key=f"csv_{key}")
    st.download_button("Download Activity Log", "\n".join(st.session_state.get("activity_log", [])),
                       file_name="simulator_activity.log", mime="text/plain", key=f"log_{key}")


def render(page):
    if page == "Milestone 3 Overview":
        st.header("System Overview")

        st.write(
            "Explore CPU scheduling and memory management "
            "through interactive operating system demonstrations."
        )

        col1, col2, col3 = st.columns(3)
        col1.metric("CPU Scheduling Policies", "5")
        col2.metric("Memory Policies", "2")
        col3.metric("CPU Timeline", "Gantt Chart")

        st.subheader("System Managers")

        managers = pd.DataFrame({
            "Manager": [
                "Process Manager",
                "Memory Manager",
                "File Manager",
                "Security Manager",
                "Device Manager",
                "Network Manager",
            ],
            "Function": [
                "CPU scheduling and process metrics",
                "Page replacement and memory frames",
                "File operations and storage",
                "Access control and permissions",
                "Device allocation and I/O",
                "Network resource management",
            ],
            "Status": [
        "Demo available",
        "Demo available",
        "Demo available",
        "Not implemented",
        "Not implemented",
        "Not implemented",
    ],
        })

        st.dataframe(
            managers,
            use_container_width=True,
            hide_index=True,
        )

        st.info(
            "Only components marked 'Demo available' have "
            "working demonstrations in this version."
        )


    # ==================================================
    # PROCESS MANAGER
    # ==================================================

    elif page == "CPU Scheduling (Updated)":
        st.header("Process Manager")

        st.write(
            "Edit the processes, choose a scheduling policy, "
            "and view the resulting CPU Gantt chart and metrics."
        )

        st.subheader("Process Input")

        process_input = st.data_editor(
            DEFAULT_PROCESSES,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            key="process_table",
            column_config={
                "Process": st.column_config.TextColumn(
                    "Process ID",
                    required=True,
                ),
                "Arrival": st.column_config.NumberColumn(
                    "Arrival Time",
                    min_value=0,
                    step=1,
                    required=True,
                ),
                "Burst": st.column_config.NumberColumn(
                    "Burst Time",
                    min_value=1,
                    step=1,
                    required=True,
                ),
                "Priority": st.column_config.NumberColumn(
                    "Priority",
                    min_value=1,
                    step=1,
                    required=True,
                ),
            },
        )

        st.caption(
            "Lower priority numbers indicate higher priority. "
            "Arrival and burst times use whole-number time units."
        )

        col1, col2 = st.columns(2)

        with col1:
            policy = st.selectbox(
                "Scheduling Algorithm",
                ["FCFS", "SJF", "SRTF", "Round Robin", "Priority"],
            )

        with col2:
            quantum = st.number_input(
                "Round Robin Time Quantum",
                min_value=1,
                max_value=100,
                value=4,
                step=1,
                disabled=policy != "Round Robin",
            )

        run_cpu = st.button(
            "Run Scheduling Simulation",
            type="primary",
            use_container_width=True,
        )

        if run_cpu:
            try:
                if process_input.empty:
                    st.error("Add at least one process.")
                    st.stop()

                data = process_input.copy()

                if data.isnull().any().any():
                    st.error("Fill in every process field.")
                    st.stop()

                data["Process"] = data["Process"].astype(str).str.strip()

                if (data["Process"] == "").any():
                    st.error("Process IDs cannot be blank.")
                    st.stop()

                if data["Process"].duplicated().any():
                    st.error("Each process must have a unique ID.")
                    st.stop()

                for column in ["Arrival", "Burst", "Priority"]:
                    numeric = pd.to_numeric(data[column], errors="coerce")

                    if numeric.isnull().any():
                        st.error(f"{column} must contain valid numbers.")
                        st.stop()

                    if (numeric % 1 != 0).any():
                        st.error(f"{column} must contain whole numbers.")
                        st.stop()

                    data[column] = numeric.astype(int)

                if (data["Arrival"] < 0).any():
                    st.error("Arrival times cannot be negative.")
                    st.stop()

                if (data["Burst"] < 1).any():
                    st.error("Burst times must be at least 1.")
                    st.stop()

                if (data["Priority"] < 1).any():
                    st.error("Priority values must be at least 1.")
                    st.stop()

                timeline, metrics = schedule_processes(
                    data,
                    policy,
                    int(quantum),
                )

                st.success(f"Simulation completed: {policy}")
                log_event(f"CPU simulation: {policy}, {len(data)} processes")
                st.session_state["cpu_timeline"] = pd.DataFrame(timeline)
                st.session_state["cpu_metrics"] = metrics

                display_gantt_chart(timeline)

                st.subheader("CPU Execution Intervals")

                timeline_df = pd.DataFrame(timeline)
                if not timeline_df.empty:
                    timeline_df["Duration"] = (
                        timeline_df["End"] - timeline_df["Start"]
                    )

                st.dataframe(
                    timeline_df,
                    use_container_width=True,
                    hide_index=True,
                )

                export_buttons(timeline_df, "cpu_timeline", "cpu")

                st.subheader("Process Performance Metrics")

                st.dataframe(
                    metrics,
                    use_container_width=True,
                    hide_index=True,
                )

                col1, col2 = st.columns(2)
                col1.metric(
                    "Average Waiting Time",
                    f"{metrics['Waiting'].mean():.2f}",
                )
                col2.metric(
                    "Average Turnaround Time",
                    f"{metrics['Turnaround'].mean():.2f}",
                )

                st.caption(
                    "Turnaround = Completion − Arrival. "
                    "Waiting = Turnaround − Burst."
                )

            except (ValueError, KeyError, TypeError) as error:
                st.error(f"Could not run the simulation: {error}")


    # ==================================================
    # MEMORY MANAGER
    # ==================================================

    elif page == "Memory Manager (Milestone 3)":
        st.header("Memory Manager (Milestone 3)")
        st.write(
            "Simulate page references and compare FIFO and LRU page replacement "
            "with a limited frame capacity and documented latency model."
        )
        st.caption(
            f"Latency Model: Hit = {HIT_LATENCY_NS} ns | "
            f"Fault (No Eviction) = {FAULT_NO_EVICT_LATENCY_NS:,} ns | "
            f"Fault (With Eviction) = {FAULT_EVICT_LATENCY_NS:,} ns"
        )

        reference_text = st.text_input(
            "Page Reference String",
            value="7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1",
            help="Enter page numbers separated by commas or spaces.",
        )

        col1, col2 = st.columns(2)
        with col1:
            frame_count = st.number_input(
                "Number of Frames",
                min_value=1,
                max_value=16,
                value=3,
                step=1,
            )
        with col2:
            memory_policy = st.selectbox(
                "Replacement Algorithm",
                ["FIFO", "LRU"],
            )

        run_memory = st.button(
            "Run Memory Simulation",
            type="primary",
            use_container_width=True,
        )

        if run_memory:
            try:
                references = parse_trace(reference_text)
                if not references:
                    st.error("Enter at least one page number.")
                    st.stop()

                sim_func = simulate_fifo if memory_policy == "FIFO" else simulate_lru
                res = sim_func(references, int(frame_count))

                history = pd.DataFrame(res["steps"])
                st.success(f"{memory_policy} simulation completed.")
                log_event(
                    f"Memory simulation: {memory_policy}, frames={frame_count}, "
                    f"faults={res['faults']}, hits={res['hits']}"
                )
                st.session_state["memory_history"] = history

                col1, col2, col3, col4, col5 = st.columns(5)
                col1.metric("Total References", res["total_references"])
                col2.metric("Page Hits", res["hits"])
                col3.metric("Page Faults", res["faults"])
                col4.metric("Evictions", res["evictions"])
                col5.metric("Latency (ns)", f"{res['simulated_latency_ns']:,}")

                st.subheader("Step-by-Step Frame State Trace")
                st.dataframe(history, use_container_width=True, hide_index=True)
                export_buttons(history, f"{memory_policy.lower()}_memory_history", "memory")

            except ValueError as error:
                st.error(f"Could not run memory simulation: {error}")

    # ==================================================
    # FILE SYSTEM DASHBOARD
    # ==================================================
    elif page == "File System":
        st.header("File System Dashboard")
        st.caption("In-memory demonstration. Connect the group's file engine when available.")
        if "virtual_fs" not in st.session_state:
            st.session_state.virtual_fs = init_file_system()
        left, right = st.columns([1, 2])
        with left:
            cmd = st.selectbox("Operation", ["ls", "mkdir", "touch", "write", "cat", "rm", "rmdir"])
            path = st.text_input("Absolute path", "/", key="fs_path")
            content = st.text_area("File contents", key="fs_contents") if cmd == "write" else ""
            if st.button("Execute File Operation", type="primary"):
                try:
                    result = fs_command(st.session_state.virtual_fs, cmd, path, content)
                    st.success(result)
                    log_event(f"File operation: {cmd} {path} OK")
                except ValueError as exc:
                    st.error(str(exc))
                    log_event(f"File operation: {cmd} {path} ERROR {exc}")
            if st.button("Reset Virtual File System"):
                st.session_state.virtual_fs = init_file_system()
                log_event("Virtual file system reset")
                st.rerun()
        with right:
            st.subheader("Directory and File Tree")
            tree_df = pd.DataFrame(fs_tree(st.session_state.virtual_fs))
            st.dataframe(tree_df, use_container_width=True, hide_index=True)
            export_buttons(tree_df, "filesystem_tree", "file")

    elif page == "Policy Comparison":
        st.header("FIFO vs. LRU Policy Comparison")
        st.caption(
            "Side-by-side performance comparison on identical address-reference traces and frame capacities."
        )

        text = st.text_input(
            "Page References",
            "7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1",
            key="comparison_ref"
        )
        frames = st.number_input("Frames", 1, 16, 3, key="comparison_frames")

        if st.button("Compare Policies", type="primary"):
            try:
                refs = parse_trace(text)
                if not refs:
                    st.error("Enter valid page references.")
                    st.stop()

                comp = compare_algorithms(refs, int(frames))
                fifo_res = comp["fifo"]
                lru_res = comp["lru"]

                rows = [
                    {
                        "Policy": "FIFO",
                        "Total References": fifo_res["total_references"],
                        "Hits": fifo_res["hits"],
                        "Faults": fifo_res["faults"],
                        "Fault Rate (%)": fifo_res["fault_rate"],
                        "Evictions": fifo_res["evictions"],
                        "Total Latency (ns)": fifo_res["simulated_latency_ns"]
                    },
                    {
                        "Policy": "LRU",
                        "Total References": lru_res["total_references"],
                        "Hits": lru_res["hits"],
                        "Faults": lru_res["faults"],
                        "Fault Rate (%)": lru_res["fault_rate"],
                        "Evictions": lru_res["evictions"],
                        "Total Latency (ns)": lru_res["simulated_latency_ns"]
                    }
                ]

                df = pd.DataFrame(rows)
                st.session_state["comparison"] = df
                st.session_state["fifo_trace"] = pd.DataFrame(fifo_res["steps"])
                st.session_state["lru_trace"] = pd.DataFrame(lru_res["steps"])
                log_event(f"Compared FIFO and LRU: frames={frames}, references={len(refs)}")

            except ValueError as exc:
                st.error(str(exc))

        if "comparison" in st.session_state:
            df = st.session_state.comparison
            st.subheader("Side-by-Side Comparison Table")
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Visual Bar Chart Comparison
            st.subheader("Visual Metric Comparison")
            chart_data = pd.DataFrame({
                "Metric": ["Page Hits", "Page Faults", "Evictions", "Page Hits", "Page Faults", "Evictions"],
                "Count": [
                    df.loc[df['Policy'] == 'FIFO', 'Hits'].values[0],
                    df.loc[df['Policy'] == 'FIFO', 'Faults'].values[0],
                    df.loc[df['Policy'] == 'FIFO', 'Evictions'].values[0],
                    df.loc[df['Policy'] == 'LRU', 'Hits'].values[0],
                    df.loc[df['Policy'] == 'LRU', 'Faults'].values[0],
                    df.loc[df['Policy'] == 'LRU', 'Evictions'].values[0],
                ],
                "Policy": ["FIFO", "FIFO", "FIFO", "LRU", "LRU", "LRU"]
            })

            fig = go.Figure()
            for pol in ("FIFO", "LRU"):
                sub = chart_data[chart_data["Policy"] == pol]
                fig.add_trace(go.Bar(name=pol, x=sub["Metric"], y=sub["Count"]))
            fig.update_layout(barmode="group", title="FIFO vs LRU Page Outcomes")
            st.plotly_chart(fig, use_container_width=True)

            export_buttons(df, "fifo_lru_comparison", "comparison")

            col_tr1, col_tr2 = st.columns(2)
            with col_tr1:
                st.subheader("FIFO Frame Trace")
                st.dataframe(st.session_state["fifo_trace"], hide_index=True, use_container_width=True)
            with col_tr2:
                st.subheader("LRU Frame Trace")
                st.dataframe(st.session_state["lru_trace"], hide_index=True, use_container_width=True)

    elif page == "Dashboard Tests":
        st.header("Dashboard Test Controls")
        st.caption("These are dashboard smoke tests, not the full group's automated test suite.")
        if st.button("Run Dashboard Tests", type="primary"):
            st.session_state.test_results = run_dashboard_tests()
            log_event("Dashboard smoke tests executed")
        if "test_results" in st.session_state:
            df = st.session_state.test_results
            st.metric("Tests Passed", f"{(df['Status'] == 'PASS').sum()} / {len(df)}")
            st.dataframe(df, hide_index=True, use_container_width=True)
            export_buttons(df, "dashboard_tests", "tests")

    elif page == "Exports":
        st.header("CSV and Log Export Center")
        available = {
            "CPU timeline": "cpu_timeline", "CPU metrics": "cpu_metrics",
            "Memory history": "memory_history", "Policy comparison": "comparison",
            "File tree": "virtual_fs", "Dashboard tests": "test_results",
        }
        for label, key in available.items():
            if key in st.session_state:
                df = (pd.DataFrame(fs_tree(st.session_state[key])) if key == "virtual_fs"
                      else st.session_state[key])
                st.download_button(f"Download {label} CSV", df.to_csv(index=False),
                                   file_name=key + ".csv", mime="text/csv", key="export_" + key)
        st.download_button("Download Full Activity Log", "\n".join(st.session_state.get("activity_log", [])),
                           file_name="simulator_activity.log", mime="text/plain", key="export_log")
        st.caption("Run simulations or tests to populate additional exports.")

