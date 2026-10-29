# IoT Sensor Data Queue Manager

A beginner-friendly micro-project with simulated IoT readings, priority-based queueing, data processing, SQLite persistence, and a Streamlit dashboard.

## Features
- Simulated temperature, humidity, and air-quality sensors
- Priority-first processing and FIFO normal queue
- SQLite storage for processed readings
- Interactive Plotly charts and dashboard filters
- CSV export and processing-time analytics

## Run on Windows (PowerShell)

Open PowerShell in this folder and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL Streamlit prints (usually http://localhost:8501).

## How to use
1. Use the sidebar to generate sensor readings.
2. Click **Process Pending Queue** to process and store them.
3. Explore Overview, Live Monitoring, Queue Management, Data History, and Performance Analytics.
4. Export filtered history as CSV from Data History.

## Notes
- The sensors are simulated in software; no physical hardware is required.
- The queue is in memory and resets when the Streamlit process restarts.
- Processed history is stored in `iot_sensor_data.db` in this project folder.
