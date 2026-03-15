import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
import os
import sys
import boto3
import numpy as np
from datetime import datetime, timezone

# --- PATH SETUP ---
current_file = os.path.abspath(__file__)
views_dir = os.path.dirname(current_file)
frontend_dir = os.path.dirname(views_dir)     # for frontend
project_root = os.path.dirname(frontend_dir)  # for backend
core_system_dir = os.path.join(project_root, "core_system")

if core_system_dir not in sys.path: 
    sys.path.insert(0, core_system_dir)
if project_root not in sys.path: 
    sys.path.insert(0, project_root)

from core_system.metrics_collector import get_lambda_metrics
from core_system.smartscale_core import SmartScaleSystem

@st.cache_resource
def load_ai_brain(): return SmartScaleSystem()
brain = load_ai_brain()

@st.cache_data(ttl=60)
def fetch_aws_data(name, ak, sk, reg): return get_lambda_metrics(name, ak, sk, reg)

def scale_aws_resource(replicas, access_key, secret_key, region, function_name):
    try:
        client = boto3.client('lambda', aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)
        client.put_provisioned_concurrency_config(FunctionName=function_name, Qualifier='PROD', ProvisionedConcurrentExecutions=int(replicas))
        return True
    except Exception as e: return False

st.title("SmartScale Live Production Manager")

if 'aws_access' not in st.session_state or not st.session_state['aws_access']:
    st.warning("Please configure your AWS keys in the **Cloud Settings** page.")
    st.stop()

# Persistent Toggle State
# Create a permanent memory spot for the toggle if it doesn't exist
if 'scaling_active' not in st.session_state:
    st.session_state['scaling_active'] = False

# Callback function to save the toggle's position when clicked
def save_toggle_state():
    st.session_state['scaling_active'] = st.session_state.toggle_widget

# Create the toggle linked to the permanent memory
live_mode = st.toggle(
    "Enable Proactive Auto-Scaling (AI Manager)", 
    value=st.session_state['scaling_active'], 
    key="toggle_widget",
    on_change=save_toggle_state
)
if 'live_logs' not in st.session_state: st.session_state.live_logs = pd.DataFrame(columns=["time", "actual_load", "predicted_load", "replicas", "decision"])
if 'last_scaled_replica' not in st.session_state: st.session_state['last_scaled_replica'] = 1

dashboard_placeholder = st.empty()

# --- LIVE LOOP ---
while True:
    ak = st.session_state['aws_access']
    sk = st.session_state['aws_secret']
    reg = st.session_state['aws_region']
    func = st.session_state['aws_func']
    
    ts, counts = fetch_aws_data(func, ak, sk, reg)
    
    if len(ts) > 0:
        latest_time_str = ts[-1].strftime("%H:%M:%S")
        latest_actual = counts[-1]
        
        is_new_data = st.session_state.live_logs.empty or st.session_state.live_logs.iloc[-1]['time'] != latest_time_str
        if is_new_data:
            live_pred = brain.predict_live_load(list(counts), datetime.now(timezone.utc))
            replicas = max(1, int(np.ceil(live_pred / 50.0)))
            
            last_rep = st.session_state['last_scaled_replica']
            if replicas > last_rep: decision = "SCALE UP ⬆️"
            elif replicas < last_rep: decision = "SCALE DOWN 🔽"
            else: decision = "MAINTAIN ✅"
            
            if live_mode and replicas != last_rep:
                success = scale_aws_resource(replicas, ak, sk, reg, func)
                if success: st.session_state['last_scaled_replica'] = replicas
                    
            new_row = pd.DataFrame([{"time": latest_time_str, "actual_load": latest_actual, "predicted_load": live_pred, "replicas": replicas, "decision": decision}])
            st.session_state.live_logs = pd.concat([st.session_state.live_logs, new_row], ignore_index=True)

    with dashboard_placeholder.container():
        df = st.session_state.live_logs
        if df.empty:
            st.info("Waiting for AWS CloudWatch data... (Make sure your Lambda has traffic).")
        else:
            latest = df.iloc[-1]
            decision = latest['decision']
            color, icon = ("red", "🔥") if "UP" in decision else ("green", "✅") if "DOWN" in decision else ("blue", "💤")
            
            with st.container(border=True):
                c_status, c_metrics = st.columns([1, 3])
                with c_status:
                    st.markdown(f"### {icon}")
                    st.markdown(f"**Status:** :{color}[{decision}]")
                    if live_mode: st.caption("📡 *AI Executing on AWS*")
                    else: st.caption("🕶️ *Advisor Mode (No Execution)*")
                
                with c_metrics:
                    m1, m2, m3 = st.columns(3)
                    with m1: st.metric("Live AWS Invocations", f"{latest['actual_load']:.0f}")
                    with m2: st.metric("AI Predicted Invocations", f"{latest['predicted_load']:.0f}", delta=f"{latest['predicted_load']-latest['actual_load']:.0f}")
                    with m3: st.metric("AWS Active Replicas", latest['replicas'])
            
            chart_df = df.tail(60) 
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=chart_df['time'], y=chart_df['actual_load'], mode='lines', name='Actual Traffic', fill='tozeroy', line=dict(color='#00a8ff')))
            fig.add_trace(go.Scatter(x=chart_df['time'], y=chart_df['predicted_load'], mode='lines', name='Predicted Traffic', line=dict(color='#ff4757', dash='dash')))
            fig.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0), xaxis_title="Time", yaxis_title="CloudWatch Invocations")
            st.plotly_chart(fig, use_container_width=True, key=f"chart_{time.time()}")

            st.markdown("### 📜 Real-Time AWS Scaling Logs")
            st.dataframe(df.iloc[::-1].head(15), use_container_width=True, hide_index=True)
            
    time.sleep(1)