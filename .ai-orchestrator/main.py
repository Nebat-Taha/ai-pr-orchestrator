# -----------------------------------------------------------------------------
# SERVICE: AI Infrastructure Orchestrator (Main Entry Point)
#
# PURPOSE: This FastAPI application serves as the central hub for the AI-driven 
#          automation pipeline. It receives Jira webhooks, orchestrates LLM 
#          logic via Ollama, and manages downstream service calls.
#
# ARCHITECTURE: 
#   - FastAPI: Handles incoming webhooks and provides an async background task runner.
#   - PromptService: Dynamically selects the system context based on Jira labels.
#   - Ollama (Phi-3): Generates HCL/Terraform code from natural language tickets.
#   - GitHubService: Handles the Git flow (branch, commit, Pull Request).
#   - JiraService: Closes the feedback loop by reporting the PR link back to Jira.
#
# WORKFLOW:
#   1. Receives Jira Webhook -> 2. Extracts Ticket Metadata -> 3. Triggers 
#   Background Orchestration -> 4. Calls LLM -> 5. Pushes to Git -> 6. Comments on Jira.
#
# License: MIT License
# Copyright (c) 2026 Nebat Taha
# All rights reserved.
# -----------------------------------------------------------------------------
# -----------------------------------------------------------------------------
# SERVICE: AI Infrastructure Orchestrator (Main Entry Point)
#
# PURPOSE: This FastAPI application serves as the central hub for the AI-driven 
#          automation pipeline. It receives Jira webhooks, orchestrates LLM 
#          logic via Ollama, and manages downstream service calls.
#
# ARCHITECTURE: 
#   - Dynamic Pathing: Now supports AI-driven directory structures by parsing
#     the 'PATH:' and 'CODE:' markers from the LLM response.
#
# License: MIT License
# Copyright (c) 2026 Nebat Taha
# All rights reserved.
# -----------------------------------------------------------------------------

import ollama
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from services.github_svc import GitHubService
from services.prompt_svc import PromptService
from services.jira_svc import JiraService

# Initialize the FastAPI app and our custom services
app = FastAPI()
gh_service = GitHubService()
prompt_svc = PromptService()
jira_svc = JiraService() 

class JiraPayload(BaseModel):
    """Schema for incoming Jira Webhook data."""
    issue: dict

def start_orchestration(ticket_id: str, summary: str, labels: list):
    """
    Background task to handle AI generation, GitHub PR, and Jira feedback.
    """
    # 1. PERSONA SELECTION: Load context from prompts/ directory
    system_prompt = prompt_svc.get_context(labels)
    
    # 2. AI GENERATION: Call local Ollama instance (Phi-3)
    # We explicitly ask for the PATH: and CODE: format in the prompt here too
    prompt_query = f"PROCESS TICKET {ticket_id}: {summary}. STRICT ADHERENCE TO SYSTEM SCHEMA REQUIRED."

    print(f"🤖 AI (Phi-3) is thinking about {ticket_id}... (Please wait)")
    try:
        response = ollama.generate(
            model='phi3',
            system=system_prompt,
            prompt=prompt_query
        )
        # 1. Capture the actual text from the response object
        raw_response = response['response'] 

        # 2. NOW apply the sanitizer to strip pre-text/babble
        if "PATH:" in raw_response:
            raw_response = raw_response[raw_response.find("PATH:"):]
       
        print(f"✅ AI finished generating {len(raw_response)} characters.") 

        # 3. DYNAMIC PATH & CODE PARSING
        # Default fallback values
        target_path = f"infrastructure/{ticket_id}.tf"
        ai_generated_code = raw_response

        if "PATH:" in raw_response and "CODE:" in raw_response:
            try:
                # Split the text into Path and Code sections
                parts = raw_response.split("CODE:")
                path_part = parts[0].replace("PATH:", "").strip()
                code_part = parts[1].strip()
                
                if path_part:
                    target_path = path_part
                ai_generated_code = code_part
                print(f"📍 AI suggested path: {target_path}")
            except Exception as e:
                print(f"⚠️ Parsing failed, using default pathing. Error: {e}")

        # 4. CODE CLEANING: Strip markdown artifacts
        ai_generated_code = (
            ai_generated_code.replace("```hcl", "")
            .replace("```terraform", "")
            .replace("```", "")
        )
        
        # 5. ISOLATE CODE: Ensure we start at a valid Terraform keyword
        keywords = ["resource", "terraform {", "module", "variable", "data"]
        start_index = -1
        for kw in keywords:
            idx = ai_generated_code.find(kw)
            if idx != -1:
                if start_index == -1 or idx < start_index:
                    start_index = idx
        
        if start_index != -1:
            ai_generated_code = ai_generated_code[start_index:]
         
    except Exception as e:
        print(f"❌ AI Generation Failed: {e}")
        return

    # 6. GITHUB OPERATIONS: Create branch and open Pull Request
    try:
        pr_url = gh_service.create_branch_and_pr(
            ticket_id=ticket_id,
            file_path=target_path, # Dynamically assigned from AI or Default
            content=ai_generated_code,
            commit_message=f"feat: AI infrastructure generation for {ticket_id}"
        )
        print(f"--- SUCCESS --- PR: {pr_url}")

        # 7. JIRA FEEDBACK: Post the PR link back to the originating ticket
        jira_status = jira_svc.add_comment(ticket_id, pr_url)
        if jira_status == 201:
            print(f"💬 Commented on Jira ticket {ticket_id}")
        else:
            print(f"⚠️ PR created, but Jira comment failed (Status: {jira_status})")

    except Exception as e:
        print(f"--- FAILED --- Error: {e}")

@app.post("/jira-webhook")
async def jira_webhook(payload: JiraPayload, background_tasks: BackgroundTasks):
    """
    Main webhook entry point. Parses the Jira payload and handsoff 
    the heavy lifting to a background worker.
    """
    issue_key = payload.issue.get("key")
    fields = payload.issue.get("fields", {})
    summary = fields.get("summary", "No summary provided")
    labels = fields.get("labels", [])
    
    print(f"Received webhook for {issue_key}")
    background_tasks.add_task(start_orchestration, issue_key, summary, labels)
    
    return {"status": "accepted", "ticket": issue_key}