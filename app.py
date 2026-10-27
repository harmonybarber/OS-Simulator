
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from collections import deque


# ==================================================
# PAGE SETUP
# ==================================================

st.set_page_config(
    page_title="OS Simulator",
    page_icon="💻",
    layout="wide",
)

st.title("Operating System Simulator")
st.caption("CPU Scheduling • Memory Management")


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
    frames = [None] * frame_count
    history = []
    fifo_pointer = 0
    last_used = {}
    faults = 0
    hits = 0

    for step, page in enumerate(reference_string):
        if page in frames:
            hits += 1
            result = "Hit"

        else:
            faults += 1
            result = "Page Fault"

            if None in frames:
                slot = frames.index(None)
            elif policy == "FIFO":
                slot = fifo_pointer
                fifo_pointer = (
                    fifo_pointer + 1
                ) % frame_count
            else:
                slot = min(
                    range(frame_count),
                    key=lambda i: last_used.get(frames[i], -1),
                )

            frames[slot] = page

        last_used[page] = step

        history.append({
            "Step": step + 1,
            "Page": page,
            "Frames": " | ".join(
                "-" if item is None else str(item)
                for item in frames
            ),
            "Result": result,
        })

    return pd.DataFrame(history), faults, hits


# ==================================================
# NAVIGATION
# ==================================================

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Choose a page",
    ["Overview", "Process Manager", "Memory Manager"],
)

st.sidebar.divider()
st.sidebar.caption("OS Simulator • Student Project")


# ==================================================
# OVERVIEW
# ==================================================

if page == "Overview":
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
            "Not implemented",
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

elif page == "Process Manager":
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

elif page == "Memory Manager":
    st.header("Memory Manager")

    st.write(
        "Simulate page references and compare FIFO and LRU "
        "page replacement with a limited number of memory frames."
    )

    reference_text = st.text_input(
        "Page Reference String",
        value="1, 2, 3, 2, 4, 1, 5, 2, 4, 5",
        help="Enter page numbers separated by commas or spaces.",
    )

    col1, col2 = st.columns(2)

    with col1:
        frame_count = st.number_input(
            "Number of Frames",
            min_value=1,
            max_value=8,
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
            tokens = reference_text.replace(",", " ").split()

            if not tokens:
                st.error("Enter at least one page number.")
                st.stop()

            if any(not token.isdigit() for token in tokens):
                st.error("Use non-negative whole numbers for pages.")
                st.stop()

            references = [int(token) for token in tokens]

            history, faults, hits = replace_pages(
                references,
                int(frame_count),
                memory_policy,
            )

            st.success("Memory simulation completed.")

            col1, col2, col3 = st.columns(3)
            col1.metric("Page Faults", faults)
            col2.metric("Page Hits", hits)
            col3.metric(
                "Page Hit Rate",
                f"{hits / len(references) * 100:.1f}%",
            )

            st.subheader("Page Replacement History")

            st.dataframe(
                history,
                use_container_width=True,
                hide_index=True,
            )

            st.caption(
                "FIFO replaces the page loaded earliest. "
                "LRU replaces the page that has not been used "
                "for the longest time."
            )

        except (ValueError, TypeError) as error:
            st.error(f"Could not run the memory simulation: {error}")

# ==================================================
# FOOTER
# ==================================================

st.divider()
st.caption(
    "OS Simulator — Educational demonstration. "
    "Some system components are not implemented yet."
)
