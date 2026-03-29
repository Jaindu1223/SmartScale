import streamlit as st
import os
import sys
import boto3
import threading
import time
import pandas as pd 

# --- PATH SETUP ---
current_file = os.path.abspath(__file__)
views_dir = os.path.dirname(current_file)
frontend_dir = os.path.dirname(views_dir)     
project_root = os.path.dirname(frontend_dir)  
core_system_dir = os.path.join(project_root, "core_system")

if core_system_dir not in sys.path: 
    sys.path.insert(0, core_system_dir)
if project_root not in sys.path: 
    sys.path.insert(0, project_root)

from core_system.smartscale_core import SmartScaleSystem
from core_system.model_extractor import extract_features_from_pth 

@st.cache_resource
def load_ai_brain(): return SmartScaleSystem()
brain = load_ai_brain()

# --- AWS BOTO3 HELPERS ---
def update_lambda_memory(access_key, secret_key, region, function_name, memory_mb):
    try:
        client = boto3.client('lambda', aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)
        valid_memory = max(128, min(10240, int(memory_mb))) 
        client.update_function_configuration(FunctionName=function_name, MemorySize=valid_memory)
        return True, valid_memory
    except Exception as e: return False, str(e)

def upload_model_to_s3(access_key, secret_key, region, file_path, original_file_name, bucket_name="smartscale-models"):
    try:
        s3_client = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)
        object_name = f"models/{original_file_name}" 
        s3_client.upload_file(file_path, bucket_name, object_name)
        return True, object_name
    except Exception as e:
        return False, str(e)

def list_deployed_models(access_key, secret_key, region, bucket_name="smartscale-models"):
    """Fetches all deployed .pth models from S3 for the inventory grid."""
    try:
        s3 = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix="models/")
        if 'Contents' in response:
            return [obj['Key'].split('/')[-1] for obj in response['Contents'] if obj['Key'].endswith('.pth')]
        return []
    except Exception as e:
        return []

def inject_demo_traffic(access_key, secret_key, region, function_name):
    """Runs silently in the background. Sends async requests for 60 seconds to trigger scaling."""
    try:
        client = boto3.client('lambda', aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)
        # Run for exactly 60 seconds, sending ~5 safe async requests per second (protects your AWS quota)
        for _ in range(60):
            for _ in range(5):
                # InvocationType='Event' means AWS receives it instantly, but Streamlit doesn't wait for a reply
                client.invoke(FunctionName=function_name, Qualifier='PROD', InvocationType='Event') 
            time.sleep(1)
    except Exception as e:
        print(f"Traffic Injection Failed: {e}")

# --- UI SETUP ---
st.set_page_config(page_title="Deploy Model", page_icon="🚀", layout="wide")
st.title("🚀 Deploy Customer Workload")
st.markdown("Upload your PyTorch model. SmartScale will automatically extract the layers, size the hardware, and push the artifact to AWS S3.")

# Check if keys are set
if 'aws_access' not in st.session_state or not st.session_state['aws_access']:
    st.warning("⚠️ Please go to the **Cloud Settings** page to enter your AWS credentials first.")
    st.stop()

ak = st.session_state['aws_access']
sk = st.session_state['aws_secret']
reg = st.session_state['aws_region']
func = st.session_state.get('aws_func', 'InferenceFunction')

customer_upload = st.file_uploader("Upload ML Model (.pth)", type=['pth'])

if st.button("⚙️ Profile & Deploy to AWS", type="primary"):
    if customer_upload:
        original_name = customer_upload.name 
        with st.spinner(f"Extracting Architecture for {original_name} and Uploading to Cloud..."):
            temp_path = os.path.join(project_root, "temp_model.pth")
            with open(temp_path, "wb") as f: f.write(customer_upload.getbuffer())
            
            try:
                layers, input_dim, hidden_dim, params, flops = extract_features_from_pth(temp_path)
                
                st.markdown("### 📊 Extracted Model Architecture")
                c1, c2, c3 = st.columns(3)
                c1.metric("Layers", layers)
                c2.metric("Parameters", f"{params / 1_000_000:.2f} M")
                c3.metric("Est. FLOPs", f"{flops / 1_000_000_000:.2f} G")
                
                predicted_ram = brain.profile_model(layers, input_dim, hidden_dim, params, flops)
                st.success(f"🧠 **AI Profiler Decision:** Sizing Lambda to **{predicted_ram} MB RAM**")

                st.text("☁️ Updating Lambda Infrastructure...")
                success_mem, result_mem = update_lambda_memory(ak, sk, reg, func, predicted_ram)
                
                st.text(f"📦 Uploading {original_name} to S3...")
                success_s3, s3_path = upload_model_to_s3(ak, sk, reg, temp_path, original_name)
                
                if success_mem and success_s3:
                    st.success(f"✅ Deployment Complete! AWS Lambda allocated {result_mem} MB and model secured at `s3://smartscale-models/{s3_path}`.")
                else: 
                    st.error(f"❌ Deployment Failed. S3 Status: {success_s3} | Lambda Status: {success_mem}")
            except Exception as e: 
                st.error(f"Error during deployment: {e}")
            finally:
                if os.path.exists(temp_path): os.remove(temp_path)

# --- DEPLOYED MODELS INVENTORY ---
st.markdown("---")
st.markdown("### 🗄️ Deployed Models Inventory (MLOps Control Plane)")
st.markdown("Manage your globally deployed AI models. Toggle Auto-Scaling to let the LSTM AI take over infrastructure management.")

deployed_models = list_deployed_models(ak, sk, reg)

if not deployed_models:
    st.info("No models currently deployed in S3.")
else:
    # Build a clean grid layout
    header1, header2, header3, header4 = st.columns([3, 2, 2, 3])
    header1.markdown("**Model Artifact (S3)**")
    header2.markdown("**Cloud Status**")
    header3.markdown("**AI Auto-Scaler**")
    header4.markdown("**Demo Controls**")
    
    for model_name in deployed_models:
        col1, col2, col3, col4 = st.columns([3, 2, 2, 3])
        
        col1.code(model_name)
        col2.markdown("🟢 Active")
        
        # Check if this model is the currently active one
        is_active = st.session_state.get('active_auto_scale_model') == model_name
        
        # 🌟 THE FIX: Clear the Home Page memory when the toggle is clicked
        if col3.toggle("Auto-Scale", value=is_active, key=f"tgl_{model_name}"):
            if st.session_state.get('active_auto_scale_model') != model_name:
                st.session_state['active_auto_scale_model'] = model_name
                st.session_state['aws_func'] = func 
                
                # WIPE THE OLD DASHBOARD LOGS CLEAN
                st.session_state.live_logs = pd.DataFrame(columns=["time", "actual_load", "predicted_load", "replicas", "decision"])
                st.session_state['last_scaled_replica'] = 1
                
                st.rerun() # Refresh the UI instantly

        elif is_active:
             # If it was active but user turned it off
             st.session_state['active_auto_scale_model'] = None

        # The Demo Traffic Button
        if col4.button("🚀 Simulate Traffic Burst", key=f"btn_{model_name}"):
            st.toast(f"Injecting 60 seconds of live AWS traffic for {model_name}...", icon="🔥")
            thread = threading.Thread(target=inject_demo_traffic, args=(ak, sk, reg, func))
            thread.daemon = True
            thread.start()