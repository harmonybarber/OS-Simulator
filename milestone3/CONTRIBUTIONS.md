# CSC301 Operating System Simulator
## Milestone 3 - Team Contribution Log

This document records the assigned roles and reported contributions of the six project team members.

### 1. LaNadia - FIFO and LRU Memory Management
- Implemented FIFO and LRU page replacement algorithms.
- Used identical memory address traces for comparison.
- Tracked frames, page faults, evictions, and simulated latency.
- Developed `engine/memory_manager.py`.
- Authored `tests/test_memory_manager.py`.

### 2. Harmony - Hierarchical File System
- Developed the in-memory hierarchical file system.
- Worked on `ls`, `mkdir`, `touch`, `write`, `cat`, `rm`, and `rmdir`.
- Addressed invalid paths, missing files, and non-empty directory errors.

### 3. Brennan - Process and System Integration
- Connected process execution with memory reference generation.
- Worked on authorized process file requests.
- Supported ready and blocked process state transitions.
- Worked on integration between system components.

### 4. Autumn - Dashboard and Visualizations
- Developed Streamlit dashboard views.
- Created FIFO and LRU comparison tables.
- Developed Plotly charts.
- Worked on CSV and activity log exports.
- Developed dashboard test controls.

### 5. Josh - Automated Testing and Results
- Developed automated tests.
- Created test traces and file system verification scripts.
- Generated results tables and comparative figures.
- Supported end-to-end testing.

### 6. Jenysis - Documentation and GitHub Release
- Prepared and maintained project documentation.
- Created the README and architecture documentation.
- Reviewed Python dependencies.
- Prepared the team contribution log.
- Reviewed the GitHub Actions workflow.
- Organized the final project submission package.

### Testing and Verification
The local automated test run executed 23 tests:
- 22 tests passed.
- 1 test failed: `test_baselines` in `test_simulator.py`.

The baseline failure should be reviewed before claiming that the complete test suite passes.

### Final Deliverables
The project package includes the application, simulation engines, dashboard components, data files, automated tests, documentation, dependencies, and GitHub Actions workflow.
