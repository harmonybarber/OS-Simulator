
# OS-Simulator

An educational operating-system simulator dashboard built with Python and Streamlit.

## Current demonstration features

- Overview dashboard and manager status table
- Process Manager with FCFS, SJF, SRTF, Round Robin, and Priority scheduling demonstrations
- Editable sample process workload and waiting/turnaround metrics
- Memory Manager with FIFO and LRU page-replacement demonstrations
- Page-reference history, hit/fault counts, and eviction information
- Sidebar navigation between the available dashboard pages

## Requirements

- Python 3.10 or newer
- pip
- Git

## Setup on macOS

1. Clone the repository or open your local project folder.
2. Open a terminal in the project folder.
3. Create a virtual environment:

   ```bash
   python3 -m venv .venv
   ```

4. Activate it:

   ```bash
   source .venv/bin/activate
   ```

5. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

6. Start the dashboard:

   ```bash
   streamlit run app.py
   ```

7. Open the local URL shown in the terminal, normally
   `http://localhost:8501`.

To stop the dashboard, return to the terminal and press `Control + C`.

## Demonstration instructions

### Overview
Review the simulation notice, manager status table, and dashboard summary.

### Process Manager
1. Open Process Manager from the sidebar.
2. Review or edit the sample processes.
3. Select a scheduling policy.
4. For Round Robin, set the time quantum.
5. Click Run scheduling simulation.
6. Review the CPU execution intervals and process metrics.

### Memory Manager
1. Open Memory Manager from the sidebar.
2. Enter a comma-separated sequence of page numbers.
3. Choose the number of frames and FIFO or LRU.
4. Click Run memory simulation.
5. Review the access history, page hits, faults, and evictions.

## Scope and limitations

This is an initial demonstration build, not a complete operating-system simulator.
The process scheduling demonstrations do not yet implement all required advanced
features, such as priority aging, dispatcher/context-switch overhead, or a graphical
time-scaled Gantt chart. The memory demonstration does not yet model full address
translation or process blocking. File, Security, Device, Network, and parallel-computing
components are not implemented in this build.

The application uses simulated sample data. It does not control the host operating
system, change host files as part of its simulation, or scan external networks.

## Development status

Update this section as the team implements, tests, and integrates additional managers.
Do not describe incomplete functionality as completed.

## Tools and AI disclosure

Document the Python and Streamlit documentation used, any other external resources,
and any AI assistance in accordance with the course's required Sourced Tools format.
Identify the code or sections affected and the team's review, modifications, and testing.

