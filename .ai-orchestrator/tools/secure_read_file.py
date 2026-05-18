import re
import os
import json

def load_scrub_policy():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Using the more descriptive filename
    # policy_path = os.path.join(base_dir, 'scrub_policy.json')
    policy_path = os.path.join(current_dir, '..', 'scrub_policy.json')
    
    if os.path.exists(policy_path):
        with open(policy_path, 'r') as f:
            return json.load(f)
    # return {"scrub_list": [], "patterns": {}}
    return {"scrub_list": []}

def secure_read_file(file_path, project_root):
    policy = load_scrub_policy()
    scrub_list = policy.get("scrub_list", [])
    
    # --- Path Validation (Layer 1) ---
    abs_path = os.path.abspath(os.path.join(project_root, file_path))
    if not abs_path.startswith(os.path.abspath(project_root)):
        return "ERROR: Path escape detected."

    try:
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return f"ERROR: {str(e)}"

    # --- Redaction Logic (Layer 2) ---
    
    # 1. Standard PII: Emails & IPs
    content = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[REDACTED_EMAIL]", content)
    content = re.sub(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "[REDACTED_IP]", content)

    # 2. AWS Account IDs (12 consecutive digits)
    content = re.sub(r"\b\d{12}\b", "[REDACTED_AWS_ID]", content)

    # 3. Secrets (Value Masking)
    # Catches: password = "value", secret: "value", --password value
    content = re.sub(r"(?i)(password|secret|token|key)(\s*[:= ]\s*)(['\"]?)(?:(?!\3).)*\3", 
                     r"\1\2\3[REDACTED_SECRET]\3", content)

    # 4. Custom Savi Terms from our new policy file
    for term in scrub_list:
        if term: # Ensure no empty strings
            # This regex finds the term even if it's part of a string like "ubuntu:pass"
            content = re.sub(re.escape(term), "[REDACTED_TERM]", content, flags=re.IGNORECASE)

    # --- Redaction Logic (Pass 3: Catching the Password in echo "user:pass") ---
    # This is a specific DevOps pattern: echo "user:password" | chpasswd
    # We look for the colon pattern common in bash credential setting
    content = re.sub(r"\[REDACTED_TERM\]:([^\s'\"|]+)", 
                     r"[REDACTED_TERM]:[REDACTED_SECRET]", content)
    
    # --- Redaction Logic (Pass 4: Standard Infrastructure IDs) ---
    content = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[REDACTED_EMAIL]", content)
    content = re.sub(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "[REDACTED_IP]", content)
    content = re.sub(r"\b\d{12}\b", "[REDACTED_AWS_ID]", content)

    return content