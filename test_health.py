import requests
import json

url = "https://telos-backend-761085171876.asia-south1.run.app/health"
print(f"Testing {url}...")
try:
    response = requests.get(url, timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text}")
except Exception as e:
    print(f"Error: {e}")

