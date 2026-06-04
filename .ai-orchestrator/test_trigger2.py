import requests

# The destination endpoint for the LOCAL FastAPI server
URL = "http://localhost:8000/jira-webhook"

# Mock data representing a Jira 'issue_updated' or 'issue_created' event.
# Key metadata (summary, labels) is used by the AI to determine the work scope.
mock_payload = {
    "issue": {
        "key": "KAN-8",
        "fields": {
            "summary": "Deploy a new ec2 instance named 'worker-node' using our internal ec2 module found in modules/ec2. The configuration file must be placed directly in the main terraform folder at 'git-driven-observability/terraform/worker.tf'.",
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