# CSC301 Combined Milestone 3 Dashboard

This project preserves the original Milestone 2 `app.py`, `components/`, `engine/`, `data/`, and `tests/` structure and adds the Milestone 3 dashboard as `milestone3_dashboard.py`.

## Run

From this folder:

```powershell
python -m pip install -r requirements.txt
python -m pip install plotly pandas
python -m streamlit run app.py
```

Original pages are unchanged: Overview, Process Manager, Memory Manager, File Manager, Security Manager, Device Manager, Network Manager, Parallel Computing, Scenario Builder, Testing Center, Results.

New pages: Milestone 3 Overview, CPU Scheduling (Updated), Memory Manager (Milestone 3), File System, Policy Comparison, Dashboard Tests, Exports.

The Memory Management engine (`engine/memory_manager.py`) is fully integrated into the `Memory Manager (Milestone 3)` and `Policy Comparison` dashboard views, while the File System tab currently serves as an in-memory demonstration until connected to the standalone file engine. Original Security, Device, and Network pages include placeholders and are not fully functional. Dashboard Tests are smoke tests, not the complete project test suite.

# Milestone 3 - Architecture & Team Contribution Log

## Architecture Overview

The OS Simulator architecture is divided into modular engines, interactive UI components, and automated verification suites:

- **Memory Management Engine (`engine/memory_manager.py`):** Implements FIFO and LRU page replacement algorithms over identical address traces, tracks step-by-step frame state transitions, records page faults and evictions, and calculates simulated nanosecond access latency.
- **Hierarchical File System (`milestone3_dashboard.py` / `components/`):** Manages an in-memory virtual directory tree supporting standard file/directory commands (`ls`, `mkdir`, `touch`, `write`, `cat`, `rm`, `rmdir`) with error handling.
- **System & Process Integration:** Connects process execution flows to memory reference traces and authorized file system I/O requests while demonstrating process ready/blocked states.
- **Dashboard & Visualizations:** Streamlit interface providing dedicated Memory Manager and File System views, side-by-side policy comparison tables, Plotly metric charts, test control panels, and CSV/log export functionality.
- **Automated Testing Suite (`tests/`):** Unit and integration testing covering algorithm accuracy, file system safety, trace parsing, boundary conditions, and execution scripts.

---

## Team Roles & Responsibilities

1. **LaNadia — FIFO and LRU Memory Management**
   - Implement FIFO and LRU page replacement algorithms.
   - Execute simulations across identical memory address traces.
   - Track frame states, page faults, and evictions step-by-step.
   - Calculate total memory access latency using nanosecond models.
   - Generate visual comparisons between replacement policies.

2. **Harmony — Hierarchical File System**
   - Build the foundation for the in-memory hierarchical file system.
   - Implement required file and directory operations (`ls`, `mkdir`, `touch`, `write`, `cat`, `rm`, `rmdir`).
   - Integrate error handling for invalid paths, missing files, and non-empty directory removals.
   - Validate file-system functionality.

3. **Brennan — Process and System Integration**
   - Connect memory management algorithms to process-generated memory address references.
   - Link authorized process file requests to the hierarchical file system.
   - Demonstrate blocked and ready process state transitions during I/O / memory events.
   - Test full cross-component integration.

4. **Autumn — Dashboard and Visualizations**
   - Develop Streamlit dashboard views for Memory Manager and File System components.
   - Create side-by-side FIFO vs. LRU policy comparison tables and Plotly bar charts.
   - Implement CSV and activity log export utilities.
   - Build interactive dashboard test control triggers.

5. **Josh — Automated Testing and Results**
   - Develop comprehensive automated test suites (`tests/`).
   - Create standard test traces and a 12+ command file-system verification script.
   - Generate evaluation results tables and comparative performance figures.
   - Perform end-to-end functionality verification.

6. **Jenysis — Documentation and GitHub Release**
   - Maintain and update `README.md` and repository architecture documentation.
   - Verify `requirements.txt` dependencies.
   - Maintain the team contribution log.
   - Verify GitHub Actions workflow setup and bundle the final submission ZIP.

---

## Team Contribution Log

| Contributor | Module / Role | Contributions & Deliverables |
| :--- | :--- | :--- |
| **LaNadia** | Memory Management | Developed `engine/memory_manager.py` with FIFO and LRU algorithms, nanosecond latency modeling (Hit: 10ns, Fault: 10,000ns / 20,000ns), reference string parsing, frame trace tracking, updated `milestone3_dashboard.py` views, and authored `tests/test_memory_manager.py`. |
| **Harmony** | File System | Built core in-memory hierarchical file structure, directory/file creation/deletion operations, and edge-case safety validation. |
| **Brennan** | Integration | Linked process execution cycles with address reference generation and file system I/O authorization queues. |
| **Autumn** | Dashboard / UX | Built Streamlit Memory & File management tabs, side-by-side metric tables, Plotly comparative bar charts, and export actions. |
| **Josh** | Testing & Scripts | Authored full automated test suite, 12+ command execution script, results tables, and performance charts. |
| **Jenysis** | Release & Docs | Managed repository structure, GitHub Actions workflows, `requirements.txt`, system documentation, and submission packaging. |

### Latency Assumptions (`engine/memory_manager.py`)
- **Page Hit:** `10 ns`
- **Page Fault (No Eviction):** `10,000 ns`
- **Page Fault (With Eviction):** `20,000 ns`

### Benchmark Results (Capacity = 3 Frames)
**Test Trace:** `7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1` (20 references)

| Policy | Total References | Page Hits | Page Faults | Fault Rate (%) | Evictions | Total Latency (ns) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **FIFO** | 20 | 5 | 15 | 75.0% | 12 | 270,050 |
| **LRU** | 20 | 8 | 12 | 60.0% | 9 | 210,080 |

## Automated Testing

Run the full unit test suite (including memory management edge cases, eviction behavior, and trace parsing) from the root directory:

```bash
python3 -m unittest discover -s tests -v
```