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
frontend_dir = os.path.dirname(views_dir)     
project_root = os.path.dirname(frontend_dir)  
core_system_dir = os.path.join(project_root, "core_system")

if core_system_dir not in sys.path: sys.path.insert(0, core_system_dir)
if project_root not in sys.path: sys.path.insert(0, project_root)

from core_system.metrics_collector import get_lambda_metrics
from core_system.smartscale_core import SmartScaleSystem

@st.cache_resource
def load_ai_brain(): return SmartScaleSystem()
brain = load_ai_brain()

@st.cache_data(ttl=15)
def fetch_aws_data(name, ak, sk, reg): return get_lambda_metrics(name, ak, sk, reg)

def scale_aws_resource(replicas, access_key, secret_key, region, function_name):
    try:
        client = boto3.client('lambda', aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)
        client.put_provisioned_concurrency_config(FunctionName=function_name, Qualifier='PROD', ProvisionedConcurrentExecutions=int(replicas))
        return True
    except Exception as e: return False

# --- UI SETUP ---
st.markdown("<h1 style='text-align: left; font-weight: 800; letter-spacing: -0.5px;'>Live Production Dashboard</h1>", unsafe_allow_html=True)

if 'aws_access' not in st.session_state or not st.session_state['aws_access']:
    warning_html = """
    <div style="
        background: rgba(255, 171, 0, 0.1); border: 1px solid rgba(255, 171, 0, 0.4); 
        border-radius: 12px; padding: 16px 20px; margin-bottom: 20px; 
        backdrop-filter: blur(10px); color: #ffca28; display: flex; align-items: center; 
        font-weight: 500; box-shadow: 0 4px 10px rgba(0,0,0,0.2);">
        <span style="font-size: 24px; margin-right: 15px;">⚠️</span>
        <span style="font-size: 16px;"><b>Authentication Required:</b> Please configure your secure AWS keys in the <b>Cloud Settings</b> page.</span>
    </div>
    """
    st.markdown(warning_html, unsafe_allow_html=True)
    st.stop()

# --- MLOPS STATE MANAGEMENT ---
func_name = st.session_state.get('aws_func', 'InferenceFunction')
active_model = st.session_state.get('active_auto_scale_model', None)
live_mode = (active_model is not None)

st.markdown(f"<p style='text-align: left; color: #b3e5fc; margin-bottom: 20px; font-size: 1.1em;'>Real-time autonomic telemetry and LSTM predictions for <code style='color: #00d4ff; background: transparent;'>{func_name}</code>.</p>", unsafe_allow_html=True)

LOG_COLUMNS = ["Time", "Actual Load", "Predicted Load", "Provisioned Replicas", "AI Decision"]

if not live_mode:
    with st.container(border=True):
        st.markdown("<h3 style='text-align: center; color: #ffb74d;'>⏸️ System in Standby Mode</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>AI Auto-Scaling is currently completely disabled. No AWS resources are being modified.</p>", unsafe_allow_html=True)
        st.info("💡 Go to the **Deploy Page** and toggle 'Enable AI' on a model to start the Autonomic Manager.")
    
    st.session_state.live_logs = pd.DataFrame(columns=LOG_COLUMNS)
    st.session_state['last_scaled_replica'] = 1
    st.stop()

if 'live_logs' not in st.session_state: 
    st.session_state.live_logs = pd.DataFrame(columns=LOG_COLUMNS)
if 'last_scaled_replica' not in st.session_state: 
    st.session_state['last_scaled_replica'] = 1

with st.container(border=True):
    h1, h2, h3, h4 = st.columns(4)
    h1.markdown(f"**Active Engine:** ProactiveLSTM")
    h2.markdown(f"**Model:** `{active_model}`")
    h3.markdown(f"**☁️ Target:** AWS Lambda")
    h4.markdown(f"**🟢 Status:** Active Auto-Scaling")

ak = st.session_state['aws_access']
sk = st.session_state['aws_secret']
reg = st.session_state['aws_region']

ts, counts = fetch_aws_data(func_name, ak, sk, reg)

if len(ts) > 0:
    latest_dt = ts[-1]
    if latest_dt.tzinfo is None: latest_dt = latest_dt.replace(tzinfo=timezone.utc)
    data_age_seconds = (datetime.now(timezone.utc) - latest_dt).total_seconds()
    
    if data_age_seconds < 600:
        latest_time_str = latest_dt.strftime("%H:%M:%S")
        latest_actual = counts[-1]
        
        is_new_data = st.session_state.live_logs.empty or st.session_state.live_logs.iloc[-1]['Time'] != latest_time_str
        
        if is_new_data:
            live_pred = brain.predict_live_load(list(counts), datetime.now(timezone.utc))
            replicas = max(1, int(np.ceil(live_pred / 10.0))) 
            
            last_rep = st.session_state['last_scaled_replica']
            if replicas > last_rep: decision = "SCALE UP ⬆️"
            elif replicas < last_rep: decision = "SCALE DOWN 🔽"
            else: decision = "MAINTAIN ✅"
            
            if live_mode and replicas != last_rep:
                success = scale_aws_resource(replicas, ak, sk, reg, func_name)
                if success: st.session_state['last_scaled_replica'] = replicas
                    
            new_row = pd.DataFrame([{
                "Time": latest_time_str, 
                "Actual Load": latest_actual, 
                "Predicted Load": round(live_pred, 1), 
                "Provisioned Replicas": replicas, 
                "AI Decision": decision
            }])
            st.session_state.live_logs = pd.concat([st.session_state.live_logs, new_row], ignore_index=True)

# --- RENDERING THE UI ---
df = st.session_state.live_logs
if df.empty:
    st.info("📡 Connecting to AWS CloudWatch... Waiting for the first 60-second metric aggregation bucket.")
    with st.spinner("Establishing secure connection to AWS telemetry..."):
        time.sleep(2)
else:
    latest = df.iloc[-1]
    decision = latest['AI Decision']
    color, icon = ("#ff4757", "🔥") if "UP" in decision else ("#2ed573", "✅") if "DOWN" in decision else ("#00d4ff", "⚖️")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        with st.container(border=True):
            st.markdown(f"<h4 style='text-align: center; margin-bottom: 0px;'>{icon} AI Action</h4>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align: center; color: {color}; margin-top: 0px;'>{decision}</h3>", unsafe_allow_html=True)
    with c2:
        with st.container(border=True):
            st.metric("Live AWS Invocations", f"{latest['Actual Load']:.0f}")
    with c3:
        with st.container(border=True):
            st.metric("AI Predicted Traffic", f"{latest['Predicted Load']:.0f}", delta=f"{latest['Predicted Load']-latest['Actual Load']:.0f} offset")
    with c4:
        with st.container(border=True):
            st.metric("AWS Active Replicas", int(latest['Provisioned Replicas']))
    
    chart_df = df.tail(60) 
    
    # splitted charts
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("<h5 style='text-align: center; color: #00d4ff;'>📡 Actual Live Traffic</h5>", unsafe_allow_html=True)
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=chart_df['Time'], y=chart_df['Actual Load'], mode='lines', name='Actual Traffic', fill='tozeroy', line=dict(color='#00d4ff', width=3), fillcolor='rgba(0, 212, 255, 0.15)'))
        fig1.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#e0e0e0', size=12), showlegend=False, xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', title="Invocations"))
        st.plotly_chart(fig1, use_container_width=True, key="chart1")
        
    with chart_col2:
        st.markdown("<h5 style='text-align: center; color: #ff4757;'>🧠 LSTM AI Predictions</h5>", unsafe_allow_html=True)
        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(x=chart_df['Time'], y=chart_df['Predicted Load'], mode='lines', name='Predicted Load', line=dict(color='#ff4757', dash='dash', width=3)))
        fig2.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#e0e0e0', size=12), showlegend=False, xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', title="Predicted Load"))
        st.plotly_chart(fig2, use_container_width=True, key="chart2")

    st.markdown("### Real-Time AWS Scaling Logs")
    with st.container(border=True):
        display_df = df[LOG_COLUMNS].copy()
        st.dataframe(
            display_df.iloc[::-1].head(15), 
            use_container_width=True, hide_index=True,
            column_config={
                "Time": st.column_config.TextColumn("Time"),
                "Actual Load": st.column_config.NumberColumn("Actual Traffic", format="%d"),
                "Predicted Load": st.column_config.NumberColumn("AI Prediction", format="%.1f"),
                "Provisioned Replicas": st.column_config.ProgressColumn("Active Servers ☁️", format="%d", min_value=0, max_value=25),
                "AI Decision": st.column_config.TextColumn("Autonomic Action")
            }
        )

#  Instead of a permanent loop, we wait 5 seconds and then safely restart the page!
time.sleep(5)
st.rerun()