import sys
import os

# --- 1. Fix the Import Path ---
# This looks at the current folder (.ai-orchestrator) and adds the 'tools' subfolder to Python's search list
base_dir = os.path.dirname(os.path.abspath(__file__))
tools_path = os.path.join(base_dir, 'tools')
sys.path.append(tools_path)

# Now we can import the function directly
try:
    from secure_read_file import secure_read_file
except ImportError as e:
    print(f"❌ Error: Could not find secure_read_file.py in {tools_path}")
    print(f"Details: {e}")
    sys.exit(1)

# --- 2. Define Test Paths ---
# project_root is one level up from .ai-orchestrator
project_root = os.path.abspath(os.path.join(base_dir, '..'))
# Adjust this path if your test file is named differently or in a different spot
test_file_path = "git-driven-observability/terraform/security_test.tf"

def run_test():
    print("="*50)
    print("🛡️  SAVI AI-ORCHESTRATOR: REDACTION TEST")
    print("="*50)
    print(f"📂 Project Root: {project_root}")
    print(f"📄 Target File:  {test_file_path}\n")

    # Check if the test file actually exists before reading
    full_test_path = os.path.join(project_root, test_file_path)
    if not os.path.exists(full_test_path):
        print(f"❌ ERROR: Test file not found at {full_test_path}")
        print("Please ensure you created the 'security_test.tf' file in your terraform folder.")
        return

    # Run the secure reader
    output = secure_read_file(test_file_path, project_root)

    print("--- [START OF OUTPUT SENT TO LLM] ---")
    print(output)
    print("--- [END OF OUTPUT SENT TO LLM] ---")
    print("\n✅ Test execution finished.")

if __name__ == "__main__":
    run_test()