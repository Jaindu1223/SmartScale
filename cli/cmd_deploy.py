import os
import sys

# --- PATH SETUP ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path: sys.path.insert(0, project_root)

from core_system.model_extractor import extract_features_from_pth
from core_system.smartscale_core import SmartScaleSystem
from aws_utils import update_lambda_memory, upload_model_to_s3 

def execute_deploy(file_path):
    full_path = os.path.abspath(file_path)
    print(f"\n Initializing SmartScale CLI Deployment: {full_path}")
    
    if not os.path.exists(full_path):
        print(f" Error: File '{full_path}' not found.")
        return

    try:
        print("Extracting neural architecture...")
        params, flops, layers, dim = extract_features_from_pth(full_path)
        print(f"** Extracted: {params:.2f}M Params, {layers} Layers")
        
        print(" Profiling required hardware...")
        brain = SmartScaleSystem()
        predicted_ram = brain.profile_model(params, flops, layers, dim)
        
        print("Updating AWS Lambda Hardware...")
        success, result = update_lambda_memory(predicted_ram)
        
        # --- NEW S3 UPLOAD STEP ---
        print("Pushing Model Artifact to AWS S3...")
        s3_success = upload_model_to_s3(full_path)
        
        if success and s3_success:
            print(f"SUCCESS: Lambda sized to {result} MB and Model uploaded to S3!\n")
        else:
            print(f"Deployment finished with warnings. Check logs.\n")

    except Exception as e:
        print(f"Fatal Deployment Error: {e}\n")