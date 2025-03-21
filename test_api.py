import requests
import sys

url = "http://127.0.0.1:5000/execute"
data = {
    "content": "test seo",
    "keyword": "seo",
    "category": "tech",
    "topic": "ai",
    "context": "meeting"
}
print("Sending request, bro...", flush=True)
try:
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}", flush=True)
    print(f"Raw response: {response.text}", flush=True)
    print(f"JSON: {response.json()}", flush=True)
except Exception as e:
    print(f"Shit broke: {e}", flush=True)