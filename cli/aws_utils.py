import os
import boto3
from dotenv import load_dotenv

# Load AWS Keys from .env
load_dotenv()
AWS_ACCESS = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = "us-east-1"
AWS_FUNC = "InferenceFunction"
S3_BUCKET = "smartscale-models" 

if not AWS_ACCESS or not AWS_SECRET:
    print(" Error: AWS credentials not found in .env file.")
    exit(1)

def update_lambda_memory(memory_mb):
    try:
        client = boto3.client('lambda', aws_access_key_id=AWS_ACCESS, aws_secret_access_key=AWS_SECRET, region_name=AWS_REGION)
        valid_memory = max(128, min(10240, int(memory_mb)))
        client.update_function_configuration(FunctionName=AWS_FUNC, MemorySize=valid_memory)
        return True, valid_memory
    except Exception as e:
        return False, str(e)

def scale_aws_resource(replicas):
    try:
        client = boto3.client('lambda', aws_access_key_id=AWS_ACCESS, aws_secret_access_key=AWS_SECRET, region_name=AWS_REGION)
        client.put_provisioned_concurrency_config(
            FunctionName=AWS_FUNC, 
            Qualifier='PROD', 
            ProvisionedConcurrentExecutions=int(replicas)
        )
        return True
    except Exception as e:
        print(f" AWS Scaling Blocked: {e}")
        return False

# Handles dynamic file names and forces them into the "models/" folder
def upload_model_to_s3(file_path, original_file_name=None):
    """Uploads a file to an AWS S3 bucket inside the 'models/' directory."""
    
    # If no name is provided, use the fallback. Otherwise, prefix it with 'models/'
    if original_file_name is None:
        object_name = "models/customer_model.pth" 
    else:
        object_name = f"models/{original_file_name}"
        
    try:
        s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS, aws_secret_access_key=AWS_SECRET, region_name=AWS_REGION)
        s3_client.upload_file(file_path, S3_BUCKET, object_name)
        return True
    except Exception as e:
        print(f" S3 Upload Failed: {e}")
        return False