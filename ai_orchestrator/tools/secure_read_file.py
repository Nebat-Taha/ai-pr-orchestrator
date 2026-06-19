import re
import os
import json

def load_scrub_policy():
    # Absolute path calculation to bypass Windows relative path issues
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Moves up one level out of 'tools' into '.ai-orchestrator'
    orchestrator_dir = os.path.abspath(os.path.join(current_dir, ".."))
    policy_path = os.path.join(orchestrator_dir, 'scrub_policy.json')
    
    # Debug print to ensure it's looking in the right place
    if not os.path.exists(policy_path):
        print(f"⚠️ WARNING: Could not find scrub_policy.json at: {policy_path}")
        return {"scrub_list": []}
        
    with open(policy_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def secure_read_file(file_path, project_root):
    policy = load_scrub_policy()
    scrub_list = policy.get("scrub_list", [])
    
    abs_path = os.path.abspath(os.path.join(project_root, file_path))
    
    try:
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return f"ERROR: {str(e)}"

    # --- 1. Base Infrastructure Redactions ---
    content = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[REDACTED_EMAIL]", content)
    content = re.sub(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "[REDACTED_IP]", content)
    content = re.sub(r"\b\d{12}\b", "[REDACTED_AWS_ID]", content)

    # --- 2. Standard Key/Value Secrets ---
    content = re.sub(r"(?i)(password|secret|token|key)(\s*[:=]\s*)(['\"]?)(?:(?!\3).)*\3", 
                     r"\1\2\3[REDACTED_SECRET]\3", content)

    # --- 3. Custom Terms Scrubbing (e.g., ubuntu, internal-db-01) ---
    for term in scrub_list:
        if term:
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            content = pattern.sub("[REDACTED_TERM]", content)

    # --- 4. The DevOps Fallback: Catching inline passwords ---
    # This catches patterns like: [REDACTED_TERM]:SaviPassword2026! or ubuntu:SaviPassword2026!
    # It flags anything following the user target up to a quote, space, or pipeline.
    content = re.sub(r"(\[REDACTED_TERM\]|ubuntu):([^\s\"';|]+)", 
                     r"\1:[REDACTED_SECRET]", content)

    return content, None 