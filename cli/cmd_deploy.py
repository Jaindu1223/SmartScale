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
    # Extract the actual file name from the path for S3
    original_name = os.path.basename(full_path)
    
    print(f"\nInitializing SmartScale CLI Deployment: {full_path}")
    
    if not os.path.exists(full_path):
        print(f" Error: File '{full_path}' not found.")
        return

    try:
        print(" Extracting neural architecture...")
        # UPDATED: Extracting exactly 5 features
        layers, input_dim, hidden_dim, params, flops = extract_features_from_pth(full_path)
        print(f" Extracted: {params / 1_000_000:.2f}M Params, {layers} Layers, {flops / 1_000_000_000:.2f}G FLOPs")
        
        print(" Profiling required hardware...")
        brain = SmartScaleSystem()
        # UPDATED: Passing 5 features to the new Profiler
        predicted_ram = brain.profile_model(layers, input_dim, hidden_dim, params, flops)
        print(f" AI Decision: Sizing to {predicted_ram} MB RAM")
        
        print(" Updating AWS Lambda Hardware...")
        # Assuming aws_utils abstracts the keys for the CLI
        success, result = update_lambda_memory(predicted_ram)
        
        # --- NEW S3 UPLOAD STEP ---
        print(f" Pushing '{original_name}' to AWS S3...")
        # UPDATED: Passing the original_name to prevent overwriting
        s3_success = upload_model_to_s3(full_path, original_name)
        
        if success and s3_success:
            print(f" SUCCESS: Lambda sized to {result} MB and Model secured in S3!\n")
        else:
            print(f" Deployment finished with warnings. Check logs.\n")

    except Exception as e:
        print(f" Fatal Deployment Error: {e}\n")

# To allow running directly from terminal: python deploy_cli.py path/to/model.pth
if __name__ == "__main__":
    if len(sys.argv) > 1:
        execute_deploy(sys.argv[1])
    else:
        print("Usage: python deploy_cli.py <path_to_model.pth>")