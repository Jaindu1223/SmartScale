import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
import os
import sys
import threading

# --- 1. CRITICAL PATH SETUP ---
current_file = os.path.abspath(__file__)
frontend_dir = os.path.dirname(current_file)
project_root = os.path.dirname(frontend_dir)
core_system_dir = os.path.join(project_root, "core_system")

if core_system_dir not in sys.path:
    sys.path.insert(0, core_system_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from simulation_server import SmartScaleSimulator
except ImportError as e:
    st.error(f"❌ Critical Import Error: {e}")
    st.stop()

LOG_FILE = os.path.join(frontend_dir, "simulation_logs.csv")

# --- 2. START BACKGROUND SIMULATION ---
def run_simulation_background():
    try:
        sim = SmartScaleSimulator()
        sim.run()
    except Exception as e:
        print(f"Simulation Error: {e}")

if 'simulation_started' not in st.session_state:
    st.session_state['simulation_started'] = True
    if os.path.exists(LOG_FILE):
        try:
            os.remove(LOG_FILE)
        except:
            pass
    t = threading.Thread(target=run_simulation_background, daemon=True)
    t.start()

# --- 3. DASHBOARD CONFIGURATION & STYLING ---
st.set_page_config(page_title="SmartScale Dashboard", layout="wide")

# Custom CSS for "Cards" and "Grid"
st.markdown("""
<style>
    /* Metric Card Styling */
    div[data-testid="stMetric"] {
        background-color: #1E1E1E;
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #333;
    }
    h1 { text-align: center; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ SmartScale: Serverless Autonomic Manager")

# SINGLE MAIN PLACEHOLDER
dashboard_placeholder = st.empty()

def load_data():
    try:
        if os.path.exists(LOG_FILE) and os.path.getsize(LOG_FILE) > 0:
            return pd.read_csv(LOG_FILE)
        return pd.DataFrame(columns=["time", "actual_load", "predicted_load", "replicas", "decision"])
    except:
        return pd.DataFrame()

# --- 4. LIVE DASHBOARD LOOP ---
while True:
    df = load_data()
    if not df.empty:
        latest = df.iloc[-1]
        
        # Open the single placeholder to redraw everything at once
        with dashboard_placeholder.container():
            
            # === SECTION A: SMART STATUS CARD (LATEST) ===
            decision = latest['decision']
            if "UP" in decision:
                color = "red"
                icon = "🔥"
            elif "DOWN" in decision:
                color = "green"
                icon = "✅"
            else:
                color = "blue"
                icon = "💤"
            
            with st.container(border=True):
                c_status, c_metrics = st.columns([1, 3])
                
                with c_status:
                    st.markdown(f"### {icon}")
                    st.markdown(f"**Status:** :{color}[{decision}]")
                
                with c_metrics:
                    m1, m2, m3 = st.columns(3)
                    with m1: st.metric("Traffic (CPU)", f"{latest['actual_load']:.4f}")
                    with m2: st.metric("Prediction", f"{latest['predicted_load']:.4f}", delta=f"{latest['predicted_load']-latest['actual_load']:.4f}")
                    with m3: st.metric("Replicas", int(latest['replicas']))

            # === SECTION B: LIVE CHART ===
            # We only take 200 minutes. This zooms in on the recent action.
            chart_df = df.tail(2000) 
            
            fig = go.Figure()
            
            # Use 'chart_df' instead of 'df'
            fig.add_trace(go.Scatter(
                x=chart_df['time'], 
                y=chart_df['actual_load'], 
                mode='lines', 
                name='Actual', 
                fill='tozeroy', 
                line=dict(color='#00a8ff')
            ))
            
            fig.add_trace(go.Scatter(
                x=chart_df['time'], 
                y=chart_df['predicted_load'], 
                mode='lines', 
                name='Predicted', 
                line=dict(color='#ff4757', dash='dash')
            ))
            
            fig.update_layout(
                height=350, 
                margin=dict(l=0, r=0, t=10, b=0), 
                xaxis_title="Time (Last 100 Minutes)", 
                yaxis_title="CPU Load",
            )
            
            st.plotly_chart(fig, use_container_width=True, key=f"chart_{time.time()}")

             # === SECTION C: HISTORY GRID (THE LOGS) ===
            st.markdown("### 📜 Full Simulation Log History")
            
            # Using .iloc[::-1] to flip it (Newest on Top)
            history_df = df.iloc[::-1]
            
            # Display the full history with scrolling enabled
            st.dataframe(
                history_df.style.format({
                    "actual_load": "{:.4f}",
                    "predicted_load": "{:.4f}",
                    "replicas": "{:.0f}"
                }),
                use_container_width=True,
                hide_index=True,
                height=2000  
            )

    time.sleep(1)