import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
import os
import sys
import boto3
import numpy as np
from datetime import datetime, timezone
from dotenv import load_dotenv

# --- 1. CRITICAL PATH & SETUP ---
current_file = os.path.abspath(__file__)
frontend_dir = os.path.dirname(current_file)
project_root = os.path.dirname(frontend_dir)
core_system_dir = os.path.join(project_root, "core_system")

if core_system_dir not in sys.path:
    sys.path.insert(0, core_system_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from core_system.metrics_collector import get_lambda_metrics
    from core_system.smartscale_core import SmartScaleSystem
    from core_system.model_extractor import extract_features_from_pth 
except ImportError as e:
    st.error(f"❌ Critical Import Error: {e}")
    st.stop()

load_dotenv() 

# --- 2. INITIALIZE AI BRAIN (CACHED) ---
@st.cache_resource
def load_ai_brain():
    return SmartScaleSystem()

brain = load_ai_brain()

# Fetch AWS data (Caches for 60 seconds because CloudWatch updates every 60s)
@st.cache_data(ttl=60)
def fetch_aws_data(name, ak, sk, reg):
    return get_lambda_metrics(name, ak, sk, reg)

# --- 3. AWS BOTO3 HELPERS ---
def scale_aws_resource(replicas, access_key, secret_key, region, function_name):
    try:
        client = boto3.client('lambda', aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)
        client.put_provisioned_concurrency_config(
            FunctionName=function_name,
            Qualifier='PROD', 
            ProvisionedConcurrentExecutions=int(replicas)
        )
        return True
    except Exception as e:
        return False

def update_lambda_memory(access_key, secret_key, region, function_name, memory_mb):
    try:
        client = boto3.client('lambda', aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)
        valid_memory = max(128, min(10240, int(memory_mb))) 
        client.update_function_configuration(
            FunctionName=function_name,
            MemorySize=valid_memory
        )
        return True, valid_memory
    except Exception as e:
        return False, str(e)

# --- 4. DASHBOARD UI SETUP ---
st.set_page_config(page_title="SmartScale AWS Live", layout="wide")

st.markdown("""
<style>
    div[data-testid="stMetric"] { background-color: #1E1E1E; padding: 10px; border-radius: 8px; border: 1px solid #333; }
    h1 { text-align: center; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

st.title("⚡ SmartScale: AWS Live Production Manager")

# Initialize Session State to hold purely LIVE AWS Logs
if 'live_logs' not in st.session_state:
    st.session_state.live_logs = pd.DataFrame(columns=["time", "actual_load", "predicted_load", "replicas", "decision"])
if 'last_scaled_replica' not in st.session_state:
    st.session_state['last_scaled_replica'] = 1

# --- SIDEBAR: AWS CONTROLS ---
st.sidebar.title("☁️ AWS Environment")
live_mode = st.sidebar.toggle("Enable Proactive Auto-Scaling", value=False)
aws_access = st.sidebar.text_input("Access Key", value=os.getenv("AWS_ACCESS_KEY_ID", ""), type="password")
aws_secret = st.sidebar.text_input("Secret Key", value=os.getenv("AWS_SECRET_ACCESS_KEY", ""), type="password")
aws_region = st.sidebar.text_input("Region", value="us-east-1")
aws_func = st.sidebar.text_input("Lambda Function", value="InferenceFunction")

# --- SIDEBAR: CUSTOMER WORKLOAD DEPLOYMENT ---
with st.sidebar.expander("🚀 Deploy Customer Workload (.pth)", expanded=True):
    st.markdown("Upload a model to automatically size the AWS Lambda Memory.")
    customer_upload = st.file_uploader("Upload ML Model (.pth)", type=['pth'], key="cust_upload")
    
    if st.button("⚙️ Profile & Deploy"):
        if customer_upload and aws_access and aws_secret:
            with st.spinner("Extracting Architecture..."):
                temp_path = os.path.join(project_root, "temp_model.pth")
                with open(temp_path, "wb") as f:
                    f.write(customer_upload.getbuffer())
                try:
                    params, flops, layers, dim = extract_features_from_pth(temp_path)
                    st.write(f"📊 **Extracted:** {params:.2f}M Params, {layers} Layers")
                    predicted_ram = brain.profile_model(params, flops, layers, dim)
                    st.write(f"🧠 **AI Profiler:** Requires ~{predicted_ram} MB RAM")
                    
                    success, result = update_lambda_memory(aws_access, aws_secret, aws_region, aws_func, predicted_ram)
                    if success: st.success(f"✅ Lambda Memory optimized to {result} MB!")
                    else: st.error(f"❌ AWS Error: {result}")
                except Exception as e:
                    st.error(f"Error: {e}")
                finally:
                    if os.path.exists(temp_path): os.remove(temp_path)

dashboard_placeholder = st.empty()

# --- 5. LIVE DASHBOARD LOOP ---
while True:
    if aws_access and aws_secret:
        # 1. Fetch real AWS Data
        ts, counts = fetch_aws_data(aws_func, aws_access, aws_secret, aws_region)
        
        # if len(ts) > 0:
        #     latest_time = ts[-1]
        #     latest_actual = counts[-1]
            
        #     # 2. Only process if CloudWatch gave us a NEW minute of data
        #     is_new_data = st.session_state.live_logs.empty or st.session_state.live_logs.iloc[-1]['time'] != latest_time
            
        if len(ts) > 0:
            latest_time = ts[-1]
            latest_actual = counts[-1]
            
            # --- THE FIX: Convert to text string BEFORE comparing ---
            latest_time_str = latest_time.strftime("%H:%M:%S")
            
            # 2. Only process if CloudWatch gave us a NEW minute of data
            is_new_data = st.session_state.live_logs.empty or st.session_state.live_logs.iloc[-1]['time'] != latest_time_str
            if is_new_data:
                # 3. AI Predicts the future load
                # Note: datetime.utcnow() is deprecated, using timezone aware UTC
                live_pred = brain.predict_live_load(list(counts), datetime.now(timezone.utc))
                
                # Calculate Replicas (Assuming 1 replica can handle 50 invocations/min for this demo)
                replicas = max(1, int(np.ceil(live_pred / 50.0)))
                
                # Determine scaling decision
                last_rep = st.session_state['last_scaled_replica']
                if replicas > last_rep: decision = "SCALE UP ⬆️"
                elif replicas < last_rep: decision = "SCALE DOWN 🔽"
                else: decision = "MAINTAIN ✅"
                
                # 4. Act on AWS if Live Mode is ON
                if live_mode and replicas != last_rep:
                    success = scale_aws_resource(replicas, aws_access, aws_secret, aws_region, aws_func)
                    if success:
                        st.session_state['last_scaled_replica'] = replicas
                        
                # 5. Save to Session Log
                new_row = pd.DataFrame([{
                    "time": latest_time.strftime("%H:%M:%S"),
                    "actual_load": latest_actual,
                    "predicted_load": live_pred,
                    "replicas": replicas,
                    "decision": decision
                }])
                st.session_state.live_logs = pd.concat([st.session_state.live_logs, new_row], ignore_index=True)

    # --- RENDER UI ---
    with dashboard_placeholder.container():
        df = st.session_state.live_logs
        
        if df.empty:
            st.info("Waiting for AWS CloudWatch data... (Make sure your Lambda has traffic).")
        else:
            latest = df.iloc[-1]
            decision = latest['decision']
            color, icon = ("red", "🔥") if "UP" in decision else ("green", "✅") if "DOWN" in decision else ("blue", "💤")
            
            # STATUS CARD
            with st.container(border=True):
                c_status, c_metrics = st.columns([1, 3])
                with c_status:
                    st.markdown(f"### {icon}")
                    st.markdown(f"**Status:** :{color}[{decision}]")
                    if live_mode: st.caption("📡 *Synced with AWS*")
                    else: st.caption("🕶️ *Simulation Only*")
                
                with c_metrics:
                    m1, m2, m3 = st.columns(3)
                    with m1: st.metric("Live AWS Invocations", f"{latest['actual_load']:.0f}")
                    with m2: st.metric("AI Predicted Invocations", f"{latest['predicted_load']:.0f}", delta=f"{latest['predicted_load']-latest['actual_load']:.0f}")
                    with m3: st.metric("AWS Active Replicas", latest['replicas'])
            
            # LIVE CHART (Plotting the Session State Log)
            chart_df = df.tail(60) # Show last 60 minutes
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=chart_df['time'], y=chart_df['actual_load'], mode='lines', name='Actual Traffic', fill='tozeroy', line=dict(color='#00a8ff')))
            fig.add_trace(go.Scatter(x=chart_df['time'], y=chart_df['predicted_load'], mode='lines', name='Predicted Traffic', line=dict(color='#ff4757', dash='dash')))
            fig.update_layout(height=400, margin=dict(l=0, r=0, t=10, b=0), xaxis_title="Time", yaxis_title="CloudWatch Invocations")
            st.plotly_chart(fig, use_container_width=True, key=f"chart_{time.time()}")

            # HISTORY DATA
            st.markdown("### 📜 Real-Time AWS Scaling Logs")
            st.dataframe(df.iloc[::-1].head(15), use_container_width=True, hide_index=True)
            
    time.sleep(1)