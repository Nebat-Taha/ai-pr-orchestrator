import re
import os

def secure_read_file(file_path, project_root):
    # 1. Path Validation (Security)
    abs_path = os.path.abspath(os.path.join(project_root, file_path))
    if not abs_path.startswith(os.path.abspath(project_root)):
        return "ERROR: Access Denied. Path is outside of project root."

    if ".ai-orchestrator" in abs_path or "secrets" in abs_path:
        return "ERROR: Access Denied. This directory is protected."

    try:
        with open(abs_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return f"ERROR: Could not read file. {str(e)}"

    # 2. Layer 2: The Kill-Switch (Secrets Detection)
    # Simple example regex for AWS-style keys or Generic Secrets
    secret_patterns = [
        r"(?i)aws_secret_access_key\s*[:=]\s*['\"][A-Za-z0-9/+=]{40}['\"]",
        r"(?i)password\s*[:=]\s*['\"][^'\"]+['\"]"
    ]
    
    for pattern in secret_patterns:
        if re.search(pattern, content):
            # In a real scenario, this would alert DevOps/SRE
            return "SECURITY BLOCK: This file contains a hardcoded secret and cannot be processed."

    # 3. Layer 2: Redaction (PII Masking)
    # Masking Emails
    content = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[REDACTED_EMAIL]", content)
    
    # Masking IP Addresses (IPv4)
    content = re.sub(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "[REDACTED_IP]", content)

    return content

# --- Quick Test ---
if __name__ == "__main__":
    # Mocking a test
    test_content = "Contact me at devops@savi.com. The server is at 192.168.1.1"
    print("Original:", test_content)
    
    # Normally you'd pass a path, but for logic check:
    redacted = re.sub(r"[\w\.-]+@[\w\.-]+\.\w+", "[REDACTED_EMAIL]", test_content)
    redacted = re.sub(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b", "[REDACTED_IP]", redacted)
    print("Secure Output:", redacted)