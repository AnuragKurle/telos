import sys
import os

# Add client/core to path
sys.path.append(os.path.join(os.getcwd(), 'client'))

from core.firebase_auth import FirebaseAuth

config_file = 'client/config.yaml'
if not os.path.exists(config_file):
    config_file = 'config.yaml'

import yaml
with open(config_file, 'r') as f:
    config = yaml.safe_load(f)

api_key = config['firebase']['api_key']
auth = FirebaseAuth(api_key, storage_dir=".telos_test")

print(f"Testing Firebase Auth with API Key: {api_key[:10]}...")
try:
    token = auth.get_token()
    print("✓ Success! Token retrieved.")
    print(f"User ID: {auth.user_id}")
except Exception as e:
    print(f"✗ Failed: {e}")


