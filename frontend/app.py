# import streamlit as st
# import pandas as pd
# import time
# import plotly.graph_objects as go

# # --- CONFIGURATION ---
# LOG_FILE = "simulation_logs.csv"

# st.set_page_config(page_title="SmartScale Dashboard", layout="wide")
# st.title("⚡ SmartScale: Serverless Autonomic Manager")

# # Create placeholders for live updates
# kpi1, kpi2, kpi3 = st.columns(3)
# chart_placeholder = st.empty()
# decision_placeholder = st.empty()

# def load_data():
#     try:
#         # Read the CSV log file
#         df = pd.read_csv(LOG_FILE)
#         return df
#     except:
#         return pd.DataFrame(columns=["time", "actual_load", "predicted_load", "replicas", "decision"])

# # --- LIVE DASHBOARD LOOP ---
# while True:
#     df = load_data()
    
#     if not df.empty:
#         # Get latest data point
#         latest = df.iloc[-1]
        
#         # 1. Update KPI Cards
#         with kpi1:
#             st.metric("Current Traffic (CPU)", f"{latest['actual_load']:.2f}")
#         with kpi2:
#             st.metric("AI Prediction", f"{latest['predicted_load']:.2f}", delta=f"{latest['predicted_load']-latest['actual_load']:.2f}")
#         with kpi3:
#             st.metric("Active Replicas", int(latest['replicas']))

#         # 2. Update Decision Banner
#         decision = latest['decision']
#         color = "green" if "MAINTAIN" in decision else "red" if "SCALE UP" in decision else "blue"
#         decision_placeholder.markdown(f"### 📢 System Status: :{color}[{decision}]")

#         # 3. Update Chart (Live Plotly Graph)
#         fig = go.Figure()
        
#         # Plot Actual Traffic (Blue Area)
#         fig.add_trace(go.Scatter(
#             x=df['time'], y=df['actual_load'],
#             mode='lines', name='Actual Traffic',
#             fill='tozeroy', line=dict(color='#00a8ff', width=2)
#         ))
        
#         # Plot Prediction (Red Dashed Line)
#         fig.add_trace(go.Scatter(
#             x=df['time'], y=df['predicted_load'],
#             mode='lines', name='SmartScale Prediction',
#             line=dict(color='#ff4757', width=2, dash='dash')
#         ))

#         fig.update_layout(
#             title="Real-Time Traffic vs. Prediction",
#             xaxis_title="Simulation Time (Minutes)",
#             yaxis_title="CPU Load",
#             height=400,
#             margin=dict(l=0, r=0, t=30, b=0)
#         )
        
#         chart_placeholder.plotly_chart(fig, use_container_width=True)

#     # Refresh every 1 second
#     time.sleep(1)




import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
import os

# --- CONFIGURATION ---
# Log file is in the same folder as this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(BASE_DIR, "simulation_logs.csv")

st.set_page_config(page_title="SmartScale Dashboard", layout="wide")
st.title("⚡ SmartScale: Serverless Autonomic Manager")

kpi1, kpi2, kpi3 = st.columns(3)
chart_placeholder = st.empty()
decision_placeholder = st.empty()

def load_data():
    try:
        if os.path.exists(LOG_FILE):
            return pd.read_csv(LOG_FILE)
        return pd.DataFrame(columns=["time", "actual_load", "predicted_load", "replicas", "decision"])
    except:
        return pd.DataFrame()

while True:
    df = load_data()
    if not df.empty:
        latest = df.iloc[-1]
        
        with kpi1: st.metric("Current Traffic (CPU)", f"{latest['actual_load']:.2f}")
        with kpi2: st.metric("AI Prediction", f"{latest['predicted_load']:.2f}", delta=f"{latest['predicted_load']-latest['actual_load']:.2f}")
        with kpi3: st.metric("Active Replicas", int(latest['replicas']))

        decision = latest['decision']
        color = "green" if "MAINTAIN" in decision else "red" if "SCALE UP" in decision else "blue"
        decision_placeholder.markdown(f"### 📢 System Status: :{color}[{decision}]")

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['time'], y=df['actual_load'], mode='lines', name='Actual', fill='tozeroy', line=dict(color='#00a8ff')))
        fig.add_trace(go.Scatter(x=df['time'], y=df['predicted_load'], mode='lines', name='Predicted', line=dict(color='#ff4757', dash='dash')))
        fig.update_layout(title="Real-Time Traffic vs. Prediction", height=400, margin=dict(l=0, r=0, t=30, b=0))
        
        chart_placeholder.plotly_chart(fig, use_container_width=True)

    time.sleep(1)