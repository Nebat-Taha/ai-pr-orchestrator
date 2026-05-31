import os
import sys
import json
import ollama
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from services.github_svc import GitHubService
from services.prompt_svc import PromptService
from services.jira_svc import JiraService

# --- PERMANENT PATH ANCHORS ---
# Since main.py lives inside .ai-orchestrator/, its directory is our package home.
ORCHESTRATOR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(ORCHESTRATOR_DIR, '..'))

# Insert tools/ into the system path natively
tools_dir = os.path.join(ORCHESTRATOR_DIR, 'tools')
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

# --- Clean Local Module Imports ---
try:
    from generate_map import generate_repo_map
    from validate_output import verify_clean_content
    print("🛡️  All core security modules successfully linked.")
except ImportError as e:
    print(f"❌ Critical Import Error: {e}")
    sys.exit(1)

app = FastAPI()
gh_service = GitHubService()
prompt_svc = PromptService()
jira_svc = JiraService() 

class JiraPayload(BaseModel):
    issue: dict

def start_orchestration(ticket_id: str, summary: str, labels: list):
    """Background task handling JIT context gathering, secure generation, and verification."""

    # -------------------------------------------------------------------------
    # 🔍 NEW: JUST-IN-TIME REPOSITORY MAPPING
    # -------------------------------------------------------------------------
    map_json_path = os.path.join(ORCHESTRATOR_DIR, 'repo_map.json')
    print(f"\n🔍 Step 1: Evaluating repository state for {ticket_id}...")
    
    # Refresh the map (skips if file structure hash hasn't changed)
    generate_repo_map(PROJECT_ROOT, map_json_path)
    
    # Read the updated repo structure to feed to the LLM context
    try:
        with open(map_json_path, 'r', encoding='utf-8') as f:
            repo_context_tree = f.read()
    except Exception as e:
        print(f"⚠️ Failed to read repository map context: {e}")
        repo_context_tree = "{}"


    # Build prompt path relative to this self-contained directory
    prompt_path = os.path.join(ORCHESTRATOR_DIR, 'prompts')
    system_prompt = prompt_svc.get_context(labels, base_path=prompt_path)
    
    # 2. AI GENERATION CONTEXT ASSEMBLY
    # We cleanly inject the real-time file tree directly into the query prompt
    prompt_query = f"""
    PROCESS TICKET {ticket_id}: {summary}. 
    STRICT ADHERENCE TO SYSTEM SCHEMA REQUIRED.
    
    CURRENT REPOSITORY STRUCTURE:
    {repo_context_tree}
    """

    print(f"\n🤖 AI (Phi-3) is processing {ticket_id} context... (Please wait)")
    try:
        response = ollama.generate(
            model='phi3',
            system=system_prompt,
            prompt=prompt_query
        )
        raw_response = response['response'] 

        if "PATH:" in raw_response:
            raw_response = raw_response[raw_response.find("PATH:"):]
       
        print(f"✅ AI finished generating {len(raw_response)} characters.") 

        # DYNAMIC PATH & CODE PARSING
        target_path = f"infrastructure/{ticket_id}.tf"
        ai_generated_code = raw_response

        if "PATH:" in raw_response and "CODE:" in raw_response:
            try:
                parts = raw_response.split("CODE:")
                path_part = parts[0].replace("PATH:", "").strip()
                code_part = parts[1].strip()
                
                if path_part:
                    target_path = path_part
                ai_generated_code = code_part
                print(f"📍 AI suggested path: {target_path}")
            except Exception as e:
                print(f"⚠️ Parsing failed, using default pathing. Error: {e}")

        # CODE CLEANING
        ai_generated_code = (
            ai_generated_code.replace("```hcl", "")
            .replace("```terraform", "")
            .replace("```", "")
        )
        
        # ISOLATE CODE
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

    # --- OUTBOUND SECURITY GATEKEEPER LAYER ---
    print(f"🛡️  Scanning generated code for {ticket_id} before code commit...")
    is_safe, leakage_reason = verify_clean_content(ai_generated_code)
    
    if not is_safe:
        print(f"❌ SECURITY BLOCK: AI generated code contained sensitive data! Reason: {leakage_reason}")
        print("🛑 Aborting Git submission pipeline.")
        return
    
    print("✅ Security Scan Passed. Code is clean of raw infrastructure secrets.")

    # GITHUB OPERATIONS (Now targeted explicitly relative to the PROJECT_ROOT)
    try:
        pr_url = gh_service.create_branch_and_pr(
            ticket_id=ticket_id,
            file_path=target_path,
            content=ai_generated_code,
            commit_message=f"feat: AI infrastructure generation for {ticket_id}",
            repo_root=PROJECT_ROOT  # Explicit target tracking
        )
        print(f"--- SUCCESS --- PR: {pr_url}")

        jira_status = jira_svc.add_comment(ticket_id, pr_url)
        if jira_status == 201:
            print(f"💬 Commented on Jira ticket {ticket_id}")
        else:
            print(f"⚠️ PR created, but Jira comment failed (Status: {jira_status})")

    except Exception as e:
        print(f"--- FAILED --- Error: {e}")

@app.post("/jira-webhook")
async def jira_webhook(payload: JiraPayload, background_tasks: BackgroundTasks):
    issue_key = payload.issue.get("key")
    fields = payload.issue.get("fields", {})
    summary = fields.get("summary", "No summary provided")
    labels = fields.get("labels", [])
    
    print(f"\n📡 Received webhook trigger for {issue_key}")
    background_tasks.add_task(start_orchestration, issue_key, summary, labels)
    
    return {"status": "accepted", "ticket": issue_key}