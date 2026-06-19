import requests

# The destination endpoint for the LOCAL FastAPI server
URL = "http://localhost:8000/jira-webhook"

# Mock data representing a Jira 'issue_updated' or 'issue_created' event.
# Key metadata (summary, labels) is used by the AI to determine the work scope.
mock_payload = {
    "issue": {
        "key": "KAN-18",
        "fields": {
            "summary": "Read the 'modules/ec2' directory structure and then read the variables.tf file from that module to identify required inputs. Then, generate the worker.tf file using that module.",
            "labels": ["terraform", "ec2"]
        }
    }
}

try:
    print(f"🚀 Sending mock trigger for {mock_payload['issue']['key']}...")
    # Transmit the payload to the orchestrator
    response = requests.post(URL, json=mock_payload)
    
    # Evaluate the orchestrator's initial acceptance of the task
    if response.status_code == 200:
        print("✅ API accepted the request!")
        print(f"Response: {response.json()}")
    else:
        print(f"❌ Failed! Status Code: {response.status_code}")
        print(response.text)
except Exception as e:
    # Handle local connectivity issues (e.g., FastAPI server not running)
    print(f"📡 Connection Error: {e}")