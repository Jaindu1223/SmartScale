import streamlit as st
import os
import sys
import boto3
import threading
import time
import pandas as pd 

# path setup
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

# aws boto3 helpers
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
        for _ in range(60):
            for _ in range(5):
                client.invoke(FunctionName=function_name, Qualifier='PROD', InvocationType='Event') 
            time.sleep(1)
    except Exception as e:
        print(f"Traffic Injection Failed: {e}")

# ui setup
st.markdown("<h1 style='text-align: left; font-weight: 800; letter-spacing: -0.5px;'>Deploy Customer Workload</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: left; color: #b3e5fc; margin-bottom: 30px; font-size: 1.1em;'>Upload your PyTorch model. SmartScale will automatically extract the layers, size the hardware, and push the artifact to AWS S3.</p>", unsafe_allow_html=True)


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

ak = st.session_state['aws_access']
sk = st.session_state['aws_secret']
reg = st.session_state['aws_region']
func = st.session_state.get('aws_func', 'InferenceFunction')

# upload and deploy section
with st.container(border=True):
    customer_upload = st.file_uploader("Upload ML Model Artifact (.pth)", type=['pth'])
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        deploy_clicked = st.button("⚙️ Profile & Deploy to AWS", type="primary", use_container_width=True)

if deploy_clicked:
    if customer_upload:
        original_name = customer_upload.name 
        
        # Terminal-Style Status Dropdown
        with st.status(f"Initializing SmartScale Pipeline for `{original_name}`...", expanded=True) as status:
            
            st.write("📂 Saving artifact locally...")
            temp_path = os.path.join(project_root, "temp_model.pth")
            with open(temp_path, "wb") as f: f.write(customer_upload.getbuffer())
            
            try:
                st.write("🧠 AI Extracting PyTorch Architecture...")
                layers, input_dim, hidden_dim, params, flops = extract_features_from_pth(temp_path)
                
                st.write("☁️ ProfilerNN calculating hardware requirements...")
                predicted_ram = brain.profile_model(layers, input_dim, hidden_dim, params, flops)
                
                st.write(f"🌐 Provisioning AWS Lambda with {predicted_ram} MB RAM...")
                success_mem, result_mem = update_lambda_memory(ak, sk, reg, func, predicted_ram)
                
                st.write("📦 Pushing secure artifact to AWS S3...")
                success_s3, s3_path = upload_model_to_s3(ak, sk, reg, temp_path, original_name)
                
                if success_mem and success_s3:
                    status.update(label="✅ Deployment Complete & Infrastructure Provisioned!", state="complete", expanded=False)
                    
                    # Display the beautiful metrics AFTER success
                    st.markdown("### Extracted Architecture Details")
                    with st.container(border=True):
                        c1, c2, c3, c4 = st.columns(4)
                        c1.metric("Architecture Layers", layers)
                        c2.metric("Total Parameters", f"{params / 1_000_000:.2f} M")
                        c3.metric("Est. FLOPs", f"{flops / 1_000_000_000:.2f} G")
                        c4.metric("AI Assigned RAM", f"{predicted_ram} MB", delta="AWS Optimal")
                    
                    st.success(f"🎉 Model securely deployed to `s3://smartscale-models/{s3_path}`")
                else: 
                    status.update(label="❌ Deployment Failed", state="error", expanded=True)
                    st.error(f"S3 Status: {success_s3} | Lambda Status: {success_mem}")
            
            except Exception as e: 
                status.update(label="❌ Critical Error in Pipeline", state="error")
                st.error(f"Error details: {e}")
            finally:
                if os.path.exists(temp_path): os.remove(temp_path)
    else:
        st.error("⚠️ Please upload a .pth file before clicking deploy.")

# inventory of deployed models and MLOps control plane
st.markdown("<br><hr><br>", unsafe_allow_html=True)
st.markdown("### MLOps Control Plane")
st.markdown("Manage your globally deployed AI models. Toggle Auto-Scaling to let the LSTM AI take over infrastructure management.")
deployed_models = list_deployed_models(ak, sk, reg)

if not deployed_models:
    st.info("☁️ No models currently deployed in S3. Upload a model above to begin.")
else:
    header1, header2, header3, header4 = st.columns([3, 1.5, 2, 2.5])
    header1.markdown("<h4 style='color: #b3e5fc; font-size: 17px; margin-bottom: 5px;'>Artifact Name (S3)</h4>", unsafe_allow_html=True)
    header2.markdown("<h4 style='color: #b3e5fc; font-size: 17px; margin-bottom: 5px;'>Cloud Status</h4>", unsafe_allow_html=True)
    header3.markdown("<h4 style='color: #b3e5fc; font-size: 17px; margin-bottom: 5px;'>Autonomic Scaler</h4>", unsafe_allow_html=True)
    header4.markdown("<h4 style='color: #b3e5fc; font-size: 17px; margin-bottom: 5px;'>Infrastructure Test</h4>", unsafe_allow_html=True)
    
    for model_name in deployed_models:
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 1.5, 2, 2.5])
            
            with col1:
                st.markdown(f"<div style='margin-top: 10px; color: #ffffff; font-weight: 600; font-size: 16px; letter-spacing: 0.5px;'>📄 {model_name}</div>", unsafe_allow_html=True)
                
            with col2:
                st.markdown("<div style='margin-top: 10px; font-size: 16px;'><span style='color: #00e676;'>●</span> <b>Active</b></div>", unsafe_allow_html=True)
            
            with col3:
                is_active = st.session_state.get('active_auto_scale_model') == model_name
                if st.toggle("Enable AI", value=is_active, key=f"tgl_{model_name}"):
                    if st.session_state.get('active_auto_scale_model') != model_name:
                        st.session_state['active_auto_scale_model'] = model_name
                        st.session_state['aws_func'] = func 
                        
                        st.session_state.live_logs = pd.DataFrame(columns=["time", "actual_load", "predicted_load", "replicas", "decision"])
                        st.session_state['last_scaled_replica'] = 1
                        st.rerun() 
                elif is_active:
                     st.session_state['active_auto_scale_model'] = None

            with col4:
                if st.button("Inject Traffic Load", key=f"btn_{model_name}", use_container_width=True):
                    st.toast(f"Injecting 60 seconds of live AWS traffic for {model_name}...", icon="🔥")
                    thread = threading.Thread(target=inject_demo_traffic, args=(ak, sk, reg, func))
                    thread.daemon = True
                    thread.start()



                    