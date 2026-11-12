# CSC301 Operating System Simulator
## Milestone 3 - System Architecture

### 1. Project Overview
The project is an operating system simulator that demonstrates memory management, file system operations, process integration, and dashboard visualizations.

### 2. Project Structure
- `app.py` - Main application entry point.
- `milestone3_dashboard.py` - Dashboard implementation.
- `engine/` - Operating system simulation modules.
- `components/` - Dashboard components.
- `data/` - Baseline data files.
- `tests/` - Automated test files.
- `.github/workflows/` - GitHub Actions configuration.

### 3. Memory Management
The memory management modules implement FIFO and LRU page replacement simulations. The system tracks memory frames, page faults, evictions, and simulated access latency.

### 4. File System
The file system module provides an in-memory file system simulation. Its documented operations include listing, creating, writing, reading, and removing files and directories.

### 5. Process Integration
The process and integration modules connect process simulation with memory and file system functionality. Process states and resource requests are represented in the simulation.

### 6. Dashboard
The project uses Streamlit for its dashboard interface, Pandas for data handling, and Plotly for interactive visualizations.

### 7. Testing and Continuous Integration
The `tests/` directory contains automated tests. The GitHub Actions workflow is configured to run unit tests and compile Python modules when changes are pushed or pull requests are opened.

### 8. Dependencies
External Python packages are listed in `requirements.txt`:
- Streamlit
- Pandas
- Plotly

Install dependencies with:

```bash
python3 -m pip install -r requirements.txt
```

### 9. Known Limitations
The file system dashboard is currently an in-memory demonstration. Some original dashboard sections, including Security, Device, and Network, contain placeholders and are not fully functional.

### 10. Architecture Summary
The project uses a modular structure that separates simulation logic, dashboard components, data, and automated verification. This organization supports independent development of operating system features and integration through the main application.

