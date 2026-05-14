import requests

# The destination endpoint for the LOCAL FastAPI server
URL = "http://localhost:8000/jira-webhook"

# Mock data representing a Jira 'issue_updated' or 'issue_created' event.
# Key metadata (summary, labels) is used by the AI to determine the work scope.
mock_payload = {
    "issue": {
        "key": "KAN-15",
        "fields": {
            "summary": "Create a VPC with CIDR 172.16.0.0/16 and an S3 bucket. Name the S3 bucket 'data-172-16-0-0' (using the CIDR as a suffix). Place the file in terraform/regions/us-east-1/network.tf",
            "labels": ["terraform", "s3"]
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