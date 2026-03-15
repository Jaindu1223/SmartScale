import streamlit as st
import os
import sys
import boto3

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

def upload_model_to_s3(access_key, secret_key, region, file_path, bucket_name="smartscale-models"):
    """Uploads the physical .pth file to AWS S3 so the Lambda replicas can download it."""
    try:
        s3_client = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)
        object_name = "models/customer_model.pth" # This is where Lambda will look for it
        s3_client.upload_file(file_path, bucket_name, object_name)
        return True
    except Exception as e:
        return False

# --- UI SETUP ---
st.title("🚀 Deploy Customer Workload")
st.markdown("Upload your PyTorch model. SmartScale will automatically extract the layers, size the hardware, and push the artifact to AWS S3.")

# Check if keys are set
if 'aws_access' not in st.session_state or not st.session_state['aws_access']:
    st.warning("⚠️ Please go to the **Cloud Settings** page to enter your AWS credentials first.")
    st.stop()

customer_upload = st.file_uploader("Upload ML Model (.pth)", type=['pth'])

if st.button("⚙️ Profile & Deploy to AWS", type="primary"):
    if customer_upload:
        with st.spinner("Extracting Architecture and Uploading to Cloud..."):
            temp_path = os.path.join(project_root, "temp_model.pth")
            with open(temp_path, "wb") as f: f.write(customer_upload.getbuffer())
            
            try:
                # 1. Extract & Profile
                params, flops, layers, dim = extract_features_from_pth(temp_path)
                st.write(f"📊 **Extracted:** {params:.2f}M Params, {layers} Layers")
                predicted_ram = brain.profile_model(params, flops, layers, dim)
                st.write(f"🧠 **AI Profiler:** Requires ~{predicted_ram} MB RAM")
                
                # Retrieve Session Keys
                ak = st.session_state['aws_access']
                sk = st.session_state['aws_secret']
                reg = st.session_state['aws_region']
                func = st.session_state['aws_func']

                # 2. Push Hardware Config to AWS Lambda
                st.text("☁️ Updating Lambda Infrastructure...")
                success_mem, result_mem = update_lambda_memory(ak, sk, reg, func, predicted_ram)
                
                # 3. Push Physical Model to AWS S3
                st.text("📦 Uploading model artifact to S3...")
                success_s3 = upload_model_to_s3(ak, sk, reg, temp_path)
                
                # 4. Final Verification
                if success_mem and success_s3: 
                    st.success(f"✅ Deployment Complete! Lambda sized to {result_mem} MB and model secured in S3.")
                elif success_mem and not success_s3:
                    st.warning(f"⚠️ Lambda sized to {result_mem} MB, but S3 Upload Failed. Check your S3 permissions.")
                else: 
                    st.error(f"❌ AWS Error: {result_mem}")
                    
            except Exception as e: st.error(f"Error: {e}")
            finally:
                if os.path.exists(temp_path): os.remove(temp_path)