from pathlib import Path
import sys
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.queue_manager import IoTQueueManager
from core.sensor_simulator import IoTSensorSimulator
from core.data_processor import SensorDataProcessor
from database.database_manager import DatabaseManager

st.set_page_config(
    page_title="IoT Sensor Data Queue Manager",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.stApp { background: #f5f7fb; }
[data-testid="stSidebar"] { background: #fff; border-right: 1px solid #e5eaf2; }
.block-container { padding-top: 1.7rem; }
.hero { font-size: 2.15rem; font-weight: 800; color: #172554; margin-bottom: 0; }
.subhero { color: #64748b; margin: .25rem 0 1.2rem; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_system():
    queue = IoTQueueManager()
    simulator = IoTSensorSimulator()
    database = DatabaseManager()
    processor = SensorDataProcessor(queue, database)
    return queue, simulator, database, processor

queue, simulator, database, processor = get_system()

def load_data():
    records = database.get_all_readings()
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    if "timestamp" in df:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    for col in ("value", "priority", "processing_time_ms"):
        if col in df:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def generate(n):
    for _ in range(n):
        queue.add_reading(simulator.generate_reading())

def process(n=None):
    count = 0
    failed = 0
    while n is None or count + failed < n:
        result = processor.process_next()
        if result is None:
            break
        if result["status"] == "FAILED":
            failed += 1
        else:
            count += 1
    return count, failed

def priority_name(p):
    return {1: "🔴 Critical", 2: "🟠 High", 3: "🟡 Normal", 4: "🔵 Low"}.get(int(p), "Unknown")

st.sidebar.markdown("# 📡 IoT Monitor")
st.sidebar.caption("Sensor Data Queue Management")
page = st.sidebar.radio("NAVIGATION", [
    "Overview", "Live Monitoring", "Queue Management",
    "Data History", "Performance Analytics"
])
st.sidebar.divider()
st.sidebar.subheader("Simulation Controls")
n = st.sidebar.selectbox("Readings to generate", [1, 5, 10, 20, 50], index=2)
if st.sidebar.button("➕ Generate Sensor Readings", use_container_width=True):
    generate(n)
    st.session_state.notice = f"{n} simulated reading(s) added to the queue."
    st.rerun()
if st.sidebar.button("⚙️ Process Pending Queue", use_container_width=True):
    done, failed = process()
    st.session_state.notice = f"Processing complete: {done} processed, {failed} failed."
    st.rerun()
if st.sidebar.button("🔄 Refresh Dashboard", use_container_width=True):
    st.rerun()

df = load_data()
stats = queue.get_statistics()
if st.session_state.get("notice"):
    st.success(st.session_state.pop("notice"))

st.markdown('<div class="hero">IoT Sensor Data Queue Manager</div>', unsafe_allow_html=True)
st.markdown('<div class="subhero">Sensor monitoring • Priority processing • Persistent history • Performance analytics</div>', unsafe_allow_html=True)
st.caption(f"Simulation mode · Refreshed {datetime.now().strftime('%d %b %Y, %I:%M:%S %p')}")
st.divider()

if page == "Overview":
    total = len(df)
    processed = int((df["status"] == "PROCESSED").sum()) if total and "status" in df else 0
    failed = int((df["status"] == "FAILED").sum()) if total and "status" in df else 0
    a, b, c, d = st.columns(4)
    a.metric("Total Stored Readings", total)
    b.metric("Processed", processed)
    c.metric("Pending in Queue", stats["pending"])
    d.metric("Failed", failed)
    left, right = st.columns([1.5, 1])
    with left:
        st.subheader("📈 Sensor Reading Trends")
        if total:
            chart = df.dropna(subset=["timestamp", "value"]).sort_values("timestamp")
            fig = px.line(chart, x="timestamp", y="value", color="sensor_type", markers=True,
                          labels={"timestamp": "Time", "value": "Reading", "sensor_type": "Sensor"})
            fig.update_layout(template="plotly_white", height=390)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No readings saved yet. Generate readings, then process the queue.")
    with right:
        st.subheader("📊 Processing Status")
        if total:
            counts = df["status"].value_counts().rename_axis("Status").reset_index(name="Count")
            fig = px.pie(counts, names="Status", values="Count", hole=.55)
            fig.update_layout(template="plotly_white", height=390)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Status analytics appear after processing readings.")
    st.subheader("🚨 Latest Critical Readings")
    if total and "priority" in df:
        critical = df[df["priority"] == 1]
        if critical.empty:
            st.success("No critical-priority readings in saved history.")
        else:
            st.dataframe(critical[["timestamp", "sensor_id", "sensor_type", "value", "unit", "priority", "status"]].head(10),
                         use_container_width=True, hide_index=True)
    else:
        st.info("No critical readings to display yet.")

elif page == "Live Monitoring":
    st.subheader("🌡️ Sensor Monitoring")
    st.caption("These are simulated readings, not physical sensor measurements.")
    if df.empty:
        st.info("Generate and process readings to populate monitoring.")
    else:
        options = sorted(df["sensor_id"].dropna().unique())
        selected = st.multiselect("Select sensors", options, default=options)
        view = df[df["sensor_id"].isin(selected)].copy()
        if not view.empty:
            latest = view.sort_values("timestamp").groupby("sensor_id").tail(1)
            cols = st.columns(min(3, len(latest)))
            for i, (_, row) in enumerate(latest.iterrows()):
                cols[i % len(cols)].metric(row["sensor_type"], f'{row["value"]:.2f} {row["unit"]}')
            fig = px.line(view.sort_values("timestamp"), x="timestamp", y="value", color="sensor_id",
                          markers=True, hover_data=["sensor_type", "unit", "priority"])
            fig.update_layout(template="plotly_white", height=450)
            st.plotly_chart(fig, use_container_width=True)

elif page == "Queue Management":
    st.subheader("📦 Queue Management")
    st.caption("Priority 1 is highest. Priority queue readings are selected before normal FIFO readings.")
    a, b, c, d = st.columns(4)
    a.metric("Total Received", stats["total_received"])
    b.metric("Pending", stats["pending"])
    c.metric("Processed This Session", stats["processed"])
    d.metric("Failed This Session", stats["failed"])
    sizes = pd.DataFrame({"Queue": ["Priority Queue", "Normal Queue"],
                          "Readings": [stats["priority_queue_size"], stats["normal_queue_size"]]})
    fig = px.bar(sizes, x="Queue", y="Readings", text="Readings")
    fig.update_layout(template="plotly_white", height=350)
    st.plotly_chart(fig, use_container_width=True)
    st.info("Queue counters reset when the app process restarts; stored SQLite history persists.")

elif page == "Data History":
    st.subheader("🗄️ Stored Sensor Data")
    if df.empty:
        st.info("No database records yet. Generate and process readings first.")
    else:
        c1, c2, c3 = st.columns(3)
        sensor_types = sorted(df["sensor_type"].dropna().unique())
        statuses = sorted(df["status"].dropna().unique())
        priorities = sorted(df["priority"].dropna().unique())
        sensors = c1.multiselect("Sensor Type", sensor_types, default=sensor_types)
        status_filter = c2.multiselect("Status", statuses, default=statuses)
        priority_filter = c3.multiselect("Priority", priorities, default=priorities,
                                         format_func=priority_name)
        view = df[df["sensor_type"].isin(sensors) & df["status"].isin(status_filter)
                  & df["priority"].isin(priority_filter)].copy()
        shown = view.copy()
        shown["priority"] = shown["priority"].apply(priority_name)
        st.write(f"**Matching records: {len(view)}**")
        st.dataframe(shown, use_container_width=True, hide_index=True)
        st.download_button("⬇️ Export filtered records as CSV",
                           view.to_csv(index=False).encode("utf-8"),
                           file_name="iot_sensor_readings.csv", mime="text/csv")

elif page == "Performance Analytics":
    st.subheader("⚡ Processing Performance")
    if df.empty or "processing_time_ms" not in df:
        st.info("Process readings to generate performance statistics.")
    else:
        perf = df.dropna(subset=["processing_time_ms"])
        if perf.empty:
            st.info("No processing time measurements available.")
        else:
            a, b, c = st.columns(3)
            a.metric("Average", f'{perf["processing_time_ms"].mean():.3f} ms')
            b.metric("Fastest", f'{perf["processing_time_ms"].min():.3f} ms')
            c.metric("Slowest", f'{perf["processing_time_ms"].max():.3f} ms')
            fig = px.box(perf, x="sensor_type", y="processing_time_ms", color="sensor_type", points="all")
            fig.update_layout(template="plotly_white", showlegend=False, height=420)
            st.plotly_chart(fig, use_container_width=True)
            hist = px.histogram(perf, x="processing_time_ms", nbins=15, title="Processing Time Distribution")
            hist.update_layout(template="plotly_white", height=350)
            st.plotly_chart(hist, use_container_width=True)

st.divider()
st.caption("IoT Sensor Data Queue Manager · Python · Streamlit · Plotly · SQLite")
