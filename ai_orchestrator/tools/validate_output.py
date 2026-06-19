import re
import os
import json

def load_scrub_policy():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    policy_path = os.path.join(current_dir, '..', 'scrub_policy.json')
    if os.path.exists(policy_path):
        with open(policy_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"scrub_list": []}

def verify_clean_content(generated_content):
    """
    Scans AI-generated content before it hits Git.
    Returns (is_safe, leakage_reason)
    """
    policy = load_scrub_policy()
    scrub_list = policy.get("scrub_list", [])

    # 1. Check for standard patterns that should HAVE been redacted/abstracted
    if re.search(r"[\w\.-]+@[\w\.-]+\.\w+", generated_content):
        return False, "Contains unmasked Email address pattern."
        
    if re.search(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", generated_content):
        # Optional: You could exclude standard local loops like 127.0.0.1 if needed
        return False, "Contains raw IP address pattern."
        
    if re.search(r"\b\d{12}\b", generated_content):
        return False, "Contains raw 12-digit AWS Account ID."

    # 2. Check for explicit assignments (e.g., password = "something")
    # This ensures the AI isn't hardcoding a brand new secret
    if re.search(r"(?i)(password|secret|token|key)\s*[:=]\s*['\"]([^'\"\[\]]+)['\"]", generated_content):
        return False, "Contains hardcoded secret/password key-value assignment."

    # 3. Check for any forbidden custom terms from your scrub list
    for term in scrub_list:
        if term and term.lower() in generated_content.lower():
            return False, f"Contains forbidden infrastructure term: '{term}'"

    return True, "Passed security validation."