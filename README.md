# CSC301 Milestone 2 — Operating System Simulator Dashboard

## Overview
This project is a Streamlit dashboard for exploring operating system concepts through interactive simulations, charts, and performance metrics.

## Requirements
- Python 3
- Visual Studio Code (recommended)
- Internet connection for initial package installation

## Setup and Run
1. Download the project ZIP and select **Extract All**.
2. In VS Code, select **File → Open Folder** and open the extracted folder containing `app.py`.
3. Select **Terminal → New Terminal**.
4. Install the dependencies (if `requirements.txt` is included):
   ```powershell
   py -m pip install -r requirements.txt
   ```
5. Start the dashboard:
   ```powershell
   py -m streamlit run app.py
   ```
6. The dashboard should open in your browser. Otherwise, visit the local URL shown in the terminal (usually `http://localhost:8501`).

If `py` is not recognized, use `python` instead. If `requirements.txt` is not included, install Streamlit with `py -m pip install streamlit`; other packages may be needed depending on the dashboard's imports.

## Using the Dashboard
- Select a simulation section in the dashboard.
- Enter or adjust the input values, then run the simulation.
- Review the results, charts, and performance metrics.
- Open **Testing Center** and run the available tests to verify functionality.

## Collaborating
Edit your assigned files, save changes, and test your section before sharing updated files with the group. ZIP copies do not sync changes automatically; the group must merge updates into one final project.

## Stop the Dashboard
Press **Ctrl + C** in the VS Code terminal.

## Project Files
- `app.py` — Streamlit dashboard entry point
- `engine/` — simulation logic
- `components/` — dashboard components

Keep these folders and files together when sharing the project.
