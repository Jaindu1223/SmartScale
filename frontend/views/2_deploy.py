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

def upload_model_to_s3(access_key, secret_key, region, file_path, original_file_name, bucket_name="smartscale-models"):
    """Uploads the physical .pth file to AWS S3 so the Lambda replicas can download it."""
    try:
        s3_client = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)
        object_name = f"models/{original_file_name}" 
        s3_client.upload_file(file_path, bucket_name, object_name)
        return True, object_name
    except Exception as e:
        print(f"S3 Upload Error: {e}")
        return False, str(e)

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
        # Get the actual file name (e.g., 'fraud_detection_v2.pth')
        original_name = customer_upload.name 
        
        with st.spinner(f"Extracting Architecture for {original_name} and Uploading to Cloud..."):
            temp_path = os.path.join(project_root, "temp_model.pth")
            with open(temp_path, "wb") as f: f.write(customer_upload.getbuffer())
            
            try:
                # 1. Extract 5 Features from the uploaded file
                layers, input_dim, hidden_dim, params, flops = extract_features_from_pth(temp_path)
                
                st.markdown("### 📊 Extracted Model Architecture")
                c1, c2, c3 = st.columns(3)
                c1.metric("Layers", layers)
                c2.metric("Parameters", f"{params / 1_000_000:.2f} M")
                c3.metric("Est. FLOPs", f"{flops / 1_000_000_000:.2f} G")
                
                # 2. Ask the AI Profiler for the RAM
                predicted_ram = brain.profile_model(layers, input_dim, hidden_dim, params, flops)
                st.success(f"🧠 **AI Profiler Decision:** Sizing Lambda to **{predicted_ram} MB RAM**")
                
                # Retrieve Session Keys
                ak = st.session_state['aws_access']
                sk = st.session_state['aws_secret']
                reg = st.session_state['aws_region']
                func = st.session_state['aws_func']

                # 3. Push Hardware Config to AWS Lambda
                st.text("☁️ Updating Lambda Infrastructure...")
                success_mem, result_mem = update_lambda_memory(ak, sk, reg, func, predicted_ram)
                
                # 4. Push Physical Model to AWS S3
                st.text(f"📦 Uploading {original_name} to S3...")
                # UPDATED: Pass the original_name to the function
                success_s3, s3_path = upload_model_to_s3(ak, sk, reg, temp_path, original_name)
                
                # 5. Final Verification
                if success_mem and success_s3:
                    st.success(f"✅ Deployment Complete! AWS Lambda allocated {result_mem} MB and model secured at `s3://smartscale-models/{s3_path}`.")
                elif success_mem and not success_s3:
                    st.warning(f"⚠️ Lambda sized to {result_mem} MB, but S3 Upload Failed. Error: {s3_path}")
                else: 
                    st.error(f"❌ AWS Error: {result_mem}")
                    
            except Exception as e: 
                st.error(f"Error during deployment: {e}")
            finally:
                if os.path.exists(temp_path): os.remove(temp_path)