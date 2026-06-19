# -----------------------------------------------------------------------------
# SERVICE: Jira Integration & Feedback Loop
#
# PURPOSE: This service manages the automated communication back to Atlassian 
#          Jira. It ensures that the engineering workflow is transparent by 
#          updating tickets with real-time links to generated resources.
#
# ARCHITECTURE: 
#   - Jira REST API v3: Utilizes the latest Atlassian API for issue management.
#   - ADF (Atlassian Document Format): Implements a structured JSON schema for 
#     rich-text comments, ensuring compatibility with modern Jira UI.
#   - Basic Auth: Uses API Tokens for secure, stateless authentication.
#
# LOGIC:
#   - Bi-directional Linking: Connects the Jira Ticket ID to the GitHub PR URL.
#   - Status Reporting: Returns standard HTTP status codes (e.g., 201 Created) 
#     to the main orchestrator for error handling and logging.
#
# License: MIT License
# Copyright (c) 2026 Nebat Taha
# All rights reserved.
# -----------------------------------------------------------------------------
import os
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

load_dotenv()

class JiraService:
    def __init__(self):
        """
        Initializes the Jira API client with credentials from the environment.
        """
        self.auth = HTTPBasicAuth(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_API_TOKEN"))
        self.base_url = os.getenv("JIRA_BASE_URL")

    def add_comment(self, issue_key, pr_url):
        """
        Constructs a rich-text comment containing a hyperlink to the GitHub PR 
        and posts it to the specified Jira issue key.
        """
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/comment"
        # Atlassian Document Format (ADF) Payload
        payload = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {"type": "text", "text": "🤖 AI Orchestrator has generated the infrastructure code. "},
                            {"type": "text", "text": "Review the Pull Request here: "},
                            {
                                "type": "text", 
                                "text": pr_url,
                                "marks": [{"type": "link", "attrs": {"href": pr_url}}]
                            }
                        ]
                    }
                ]
            }
        }
        # Execute the POST request to the Jira REST API
        try:
            response = requests.post(url, json=payload, auth=self.auth)
            return response.status_code
        except Exception as e:
            print(f"❌ Jira API Connection Error: {e}")
            return 500