# -----------------------------------------------------------------------------
# UTILITY: Jira Webhook Simulator (Test Trigger)
#
# PURPOSE: This utility simulates an incoming HTTP POST request from a Jira 
#          Webhook. It allows for rapid, local testing of the orchestration 
#          pipeline without requiring live Jira connectivity or manual triggers.
#
# ARCHITECTURE: 
#   - Requests: Uses the Python Requests library to transmit a JSON payload 
#     to the local FastAPI endpoint.
#   - Mock Data: Implements a schema-accurate 'mock_payload' that mirrors the 
#     structure of a real Atlassian Jira webhook event.
#
# USAGE: 
#   1. Ensure the FastAPI server is running (`uvicorn main:app`).
#   2. Update the 'summary' and 'labels' in mock_payload to test different 
#      infrastructure scenarios.
#   3. Execute: `python test_trigger.py`
#
# License: MIT License
# Copyright (c) 2026 Nebat Taha
# All rights reserved.
# -----------------------------------------------------------------------------
import requests

# The destination endpoint for the LOCAL FastAPI server
URL = "http://localhost:8000/jira-webhook"

# Mock data representing a Jira 'issue_updated' or 'issue_created' event.
# Key metadata (summary, labels) is used by the AI to determine the work scope.
mock_payload = {
    "issue": {
        "key": "KAN-7",
        "fields": {
            "summary": "Create an Ansible task file to install and start the node_exporter service on target instances. The target path should be inside git-driven-observability/ansible/playbooks/install_exporters.yml.",
            "labels": ["ansible"]
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