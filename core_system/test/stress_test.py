import boto3
import threading
import time
import random
import os
from dotenv import load_dotenv

# Load credentials
load_dotenv()
aws_access = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_region = "us-east-1" 
function_name = "InferenceFunction"

print("Initializing SmartScale Stress Test...")

try:
    client = boto3.client('lambda', aws_access_key_id=aws_access, aws_secret_access_key=aws_secret, region_name=aws_region)
except Exception as e:
    print(f"Failed to connect to AWS: {e}")
    exit()

def hammer_lambda(worker_id):
    """Simulates a user constantly hitting the API."""
    while True:
        try:
            # Random delay to simulate real human traffic patterns
            time.sleep(random.uniform(0.1, 0.5)) 
            
            # Ping the PROD alias specifically
            response = client.invoke(
                FunctionName=function_name,
                Qualifier='PROD',
                InvocationType='RequestResponse' 
            )
            
            if response['StatusCode'] == 200:
                print("🟢", end="", flush=True) # Success
            else:
                print("🔴", end="", flush=True) # Error
                
        except Exception as e:
            print("⚠️", end="", flush=True) # Throttled / Access Denied
            time.sleep(2)

# Start 50 concurrent threads (50 virtual users)
print("Launching 50 concurrent workers. Press Ctrl+C to stop.")
print("Waiting for CloudWatch to register traffic (takes ~60 seconds)...\n")

threads = []
for i in range(50):
    t = threading.Thread(target=hammer_lambda, args=(i,))
    t.daemon = True
    t.start()
    threads.append(t)

try:
    while True: time.sleep(1)
except KeyboardInterrupt:
    print("\n\n Stress Test Stopped.")