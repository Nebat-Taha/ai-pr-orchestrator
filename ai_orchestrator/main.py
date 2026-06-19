"""
AI-Orchestrator: Main Execution Engine
Description: This is the central entry point for the AI-Orchestrator. It listens for 
             Jira webhooks, routes requests based on language profiles, manages the 
             LLM agentic loop (recursive tool calling), and acts as the gatekeeper 
             between LLM output and the Git repository.
             
License: MIT License
Copyright (c) 2026 Nebat Taha / Savi Finance

Architecture:
- Webhook Layer: FastAPI handles async incoming requests from Jira.
- Routing Layer: Dynamic language profiles allow for multi-language support.
- Agentic Layer: Phi-3 LLM runs in a loop, capable of requesting file reads.
- Security Layer: Inbound/Outbound sanitization and regex-based leakage detection.
"""

import os
import sys
import json
import re
import ollama
import datetime 
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from ai_orchestrator.services.github_svc import GitHubService
from ai_orchestrator.services.prompt_svc import PromptService, PersonaConfigurationError
from ai_orchestrator.services.jira_svc import JiraService
from ai_orchestrator.tools.generate_map import generate_repo_map
from ai_orchestrator.tools.secure_read_file import secure_read_file
from ai_orchestrator.tools.validate_output import verify_clean_content

ORCHESTRATOR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(ORCHESTRATOR_DIR, '..'))

app = FastAPI()
gh_service = GitHubService()
prompt_svc = PromptService()
jira_svc = JiraService() 

class JiraPayload(BaseModel):
    """Schema for incoming Jira Webhook data."""
    issue: dict

class LanguageProfileNotFoundError(Exception):
    """Custom exception to explicitly halt orchestration when language routing fails."""
    pass

def load_language_profile(target_lang: str) -> dict:
    """
    Safely reads execution specifications from the external schema.
    Enforces a strict Fail-Fast design: If the language is missing or 
    the schema is corrupted, it raises an exception to abort the pipeline immediately.
    """
    profiles_path = os.path.join(ORCHESTRATOR_DIR, 'language_profiles.json')
    
    if not os.path.exists(profiles_path):
        raise LanguageProfileNotFoundError(f"❌ CRITICAL: Language registry schema missing at {profiles_path}")

    try:
        with open(profiles_path, 'r', encoding='utf-8') as f:
            profiles = json.load(f)
            
        if target_lang in profiles:
            return profiles[target_lang]
        else:
            raise LanguageProfileNotFoundError(
                f"❌ UNKNOWN RUNTIME: The detected label target '{target_lang}' is not registered in language_profiles.json"
            )
            
    except json.JSONDecodeError as e:
        raise LanguageProfileNotFoundError(
            f"❌ CORRUPTED SCHEMA: language_profiles.json failed to parse due to a syntax error: {e}"
        )


def log_audit_trail(ticket_id, entry_type, content):
    """Writes agentic decisions and tool interactions to a ticket-specific log file."""
    # Define local path to ensure consistency
    ORCHESTRATOR_DIR = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.join(ORCHESTRATOR_DIR, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = os.path.join(log_dir, f"{ticket_id}_audit.log")
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] [{entry_type.upper()}]\n{content}\n" + "-"*40 + "\n")

def start_orchestration(ticket_id: str, summary: str, labels: list):
    """
    Agentic Multi-Pass Loop: Handles dynamic tool requests from the LLM, 
    injects sanitized context JIT, and verifies output security across languages.
    """
    # 🎯 1. DYNAMIC LANGUAGE PROFILE ROUTING (STRICT MODE)
    target_lang = None
    profiles_path = os.path.join(ORCHESTRATOR_DIR, 'language_profiles.json')
    
    if os.path.exists(profiles_path):
        try:
            with open(profiles_path, 'r', encoding='utf-8') as f:
                known_langs = json.load(f).keys()
                # Hunt for the first matching registered label context
                for label in [l.lower() for l in labels]:
                    if label in known_langs:
                        target_lang = label
                        break
        except Exception:
            print("❌ Critical failure accessing language_profiles.json configuration data.")
            return

    # If no explicitly registered label was attached to the incoming request, reject it immediately
    if not target_lang:
        print(f"🛑 ABORT: Incoming ticket {ticket_id} has no valid multi-language routing labels attached. Labels received: {labels}")
        return

    try:
        profile = load_language_profile(target_lang)
        print(f"🎯 Routing Execution Flow through Dynamic Profile: [{target_lang.upper()}]")
    except LanguageProfileNotFoundError as err:
        print(f"🛑 PIPELINE ABORTED: {err}")
        return

    # JIT Repository Mapping
    map_json_path = os.path.join(ORCHESTRATOR_DIR, 'repo_map.json')
    print(f"\n🔍 Scanning repository layout context...")
    generate_repo_map(PROJECT_ROOT, map_json_path)
    
    # print(f"DEBUG: Loading map from: {map_json_path}")

    try:
        with open(map_json_path, 'r', encoding='utf-8') as f:
            repo_context_tree = f.read()
    except Exception as e:
        repo_context_tree = "{}"

    # Load system persona prompt dynamically passing matched profile criteria
    prompt_path = os.path.join(ORCHESTRATOR_DIR, 'prompts')
    
    try:
        # FIXED: Enforce fail-fast execution using our strict custom exception handling
        system_prompt = prompt_svc.get_context(labels, base_path=prompt_path, profile_filename=profile.get("prompt_file"))
    except PersonaConfigurationError as err:
        print(f"🛑 ORCHESTRATION ABORTED (Prompt Resolution Failed): {err}")
        return
    
    # Initialize the base query
    prompt_query = f"""PROCESS TICKET {ticket_id}: {summary}. 
    STRICT ADHERENCE TO SYSTEM SCHEMA REQUIRED.
    
    CURRENT REPOSITORY STRUCTURE:
    {repo_context_tree}"""
    # Temporary Debug
    # print(f"DEBUG: Repository Context Length: {len(repo_context_tree)} characters")
    # print(f"DEBUG: Sample Context: {repo_context_tree[:500]}")
    # --- AGENTIC LOOP STATE ---
    max_loops = 3
    current_loop = 0
    conversation_history = [
        {"role": "system", "content": system_prompt}, # FIXED: Corrected capitalization typo
        {"role": "user", "content": prompt_query}
    ]
    
    ai_generated_code = ""
    # Smart extension allocation based on explicit runtime context
    default_ext = ".tf" if target_lang == "terraform" else (".yml" if target_lang == "ansible" else ".py")
    target_path = f"infrastructure/{ticket_id}{default_ext}"

    print(f"\n🧠 Starting Agentic Pipeline Execution for {ticket_id}...")

    while current_loop < max_loops:
        current_loop += 1
        print(f"🤖 [Pass {current_loop}] Invoking local model (Phi-3)...")
        
        try:
            # Native format matching Ollama's local chat structures
            response = ollama.chat(
                model='phi3',
                messages=conversation_history
            )
            raw_response = response['message']['content']
            
            # --- INSERT GUARDRAIL HERE ---
            if "CODE:" in raw_response and "TOOL_REQUEST" not in raw_response:
                print("⚠️  Guardrail triggered: AI attempted to generate code without reading files.")
                conversation_history.append({"role": "user", "content": "CRITICAL ERROR: You attempted to write code without using the READ_FILE tool first. You are FORBIDDEN from writing code until you have inspected the required module definition. READ the relevant variables.tf file now."})
                continue # This skips the rest of the loop and forces the AI to try again

            # Log the LLM's thought process
            log_audit_trail(ticket_id, "LLM_THOUGHT", raw_response)


            
            # Append the LLM's raw thoughts to history so it remembers what it said
            conversation_history.append({"role": "assistant", "content": raw_response})

            # 🛑 CHECK: Did the AI request a tool call to read a file?
            tool_match = re.search(r"TOOL_REQUEST:\s*READ_FILE\[(.*?)\]", raw_response)
            
            if tool_match:
                requested_relative_path = tool_match.group(1).strip()
                print(f"🛠️  [TOOL CALL]: Agent requested to read: {requested_relative_path}")
                # --- ADD THIS: Log the tool request ---
                log_audit_trail(ticket_id, "TOOL_REQUEST", requested_relative_path)


                # Resolve path absolute relative to PROJECT_ROOT
                full_file_path = os.path.abspath(os.path.join(PROJECT_ROOT, requested_relative_path))
                
                # Execute Inbound Guardrail Sanitizer
                print(f"🛡️  Executing Inbound Guardrail on tool target...")
                # sanitized_contents, safe_error, _ = secure_read_file(PROJECT_ROOT, full_file_path)
                result = secure_read_file(requested_relative_path, PROJECT_ROOT)

# Handle the result
                if result.startswith("ERROR:"):
                    sanitized_contents = ""
                    safe_error = result
                else:
                    sanitized_contents = result
                    safe_error = None
                # --- ADD THIS: Log what the tool actually returned ---
                log_audit_trail(ticket_id, "TOOL_RESPONSE", sanitized_contents if not safe_error else safe_error)
                
                # Feed the data right back to the LLM as a tool feedback response
                tool_feedback = f"""
                --- [TOOL RESPONSE] ---
                File Contents for '{requested_relative_path}' (Sanitized & Redacted):
                ----------------------------------------
                {sanitized_contents if not safe_error else f"Error reading file: {safe_error}"}
                ----------------------------------------
                Analyze these contents to fulfill the schema target.
                """
                conversation_history.append({"role": "user", "content": tool_feedback})
                
                # Loop back to let the LLM look at the freshly read file data
                continue

            # 🏁 SUCCESS: No tool call requested. The AI has provided its final response.
            print("✅ AI reached execution conclusion. Parsing artifact...")
            
            # Extract downstream markers
            if "PATH:" in raw_response:
                working_text = raw_response[raw_response.find("PATH:"):]
                if "CODE:" in working_text:
                    try:
                        parts = working_text.split("CODE:")
                        path_part = parts[0].replace("PATH:", "").strip()
                        code_part = parts[1].strip()
                        
                        if path_part:
                            target_path = path_part
                        ai_generated_code = code_part
                    except Exception as e:
                        print(f"⚠️  Parsing failed, utilizing defaults. Error: {e}")
                        ai_generated_code = working_text
            else:
                ai_generated_code = raw_response
                
            break  # Break out of loop since we have code

        except Exception as e:
            print(f"❌ AI Generation Exception inside loop: {e}")
            return

    if not ai_generated_code:
        print("❌ Agent pipeline closed without generating code artifacts.")
        return

    # 🧼 PLUGGABLE SCHEMA-DRIVEN CLEANING MECHANISM
    for wrapper in profile.get("wrappers", []):
        ai_generated_code = ai_generated_code.replace(wrapper, "")
    
    # Isolate Code dynamically via runtime profile keyword configurations
    start_index = -1
    for kw in profile.get("keywords", []):
        idx = ai_generated_code.find(kw)
        if idx != -1:
            if start_index == -1 or idx < start_index:
                start_index = idx
                
    if start_index != -1:
        ai_generated_code = ai_generated_code[start_index:]

    # 👇Strip out inline comments completely before the security scan
    # This prevents conversational mentions of words like 'ubuntu' from triggering a block
    clean_code_only = ""
    for line in ai_generated_code.splitlines():
        # Strip trailing comments or comment-only lines for the security gate
        stripped_line = re.sub(r'#.*$', '', line).strip()
        if stripped_line:
            clean_code_only += line + "\n"

    # 👀 Visual Inspection
    print("\n--- [RAW AI GENERATED CODE ARTIFACT] ---")
    print(ai_generated_code)
    print("----------------------------------------\n")

    # --- OUTBOUND SECURITY GATEKEEPER LAYER ---
    print(f"🛡️  Scanning generated code for {ticket_id} before code commit...")
    is_safe, leakage_reason = verify_clean_content(ai_generated_code)
    
    if not is_safe:
        print(f"❌ SECURITY BLOCK: AI generated code contained sensitive data! Reason: {leakage_reason}")
        print("🛑 Aborting Git submission pipeline.")
        return
    
    print("✅ Security Scan Passed. Code is clean of raw infrastructure secrets.")

    # GITHUB OPERATIONS
    try:
        pr_url = gh_service.create_branch_and_pr(
            ticket_id=ticket_id,
            file_path=target_path,
            content=ai_generated_code,
            commit_message=f"feat: AI dynamic {target_lang} generation for {ticket_id}",
            repo_root=PROJECT_ROOT
        )
        print(f"--- SUCCESS --- PR: {pr_url}")
        jira_svc.add_comment(ticket_id, pr_url)
    except Exception as e:
        print(f"--- FAILED --- Error: {e}")

@app.post("/jira-webhook")
async def jira_webhook(payload: JiraPayload, background_tasks: BackgroundTasks):
    """
    Main webhook entry point. Parses the Jira payload and hands off 
    the heavy lifting to a background worker.
    """
    issue_key = payload.issue.get("key")
    fields = payload.issue.get("fields", {})
    summary = fields.get("summary", "No summary provided")
    labels = fields.get("labels", [])
    
    print(f"\n📡 Received webhook trigger for {issue_key}")
    background_tasks.add_task(start_orchestration, issue_key, summary, labels)
    
    return {"status": "accepted", "ticket": issue_key}

