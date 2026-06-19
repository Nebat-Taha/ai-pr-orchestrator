import os
import sys
import json


# --- FORCE SYSTEM TO LOOK INSIDE TOOLS DIRECTORY ---
current_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.join(current_dir, 'tools')

if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

# --- Direct Module Imports ---
try:
    from generate_map import generate_repo_map
    from secure_read_file import secure_read_file
    from validate_output import verify_clean_content
except (ImportError, ModuleNotFoundError):
    # Fallback path if Python struggles with the path injection context
    try:
        from tools.generate_map import generate_repo_map
        from tools.secure_read_file import secure_read_file
        from tools.validate_output import verify_clean_content
    except (ImportError, ModuleNotFoundError) as e:
        print("❌ CRITICAL IMPORT ERROR: Could not locate tool modules.")
        print(f"Details: {e}")
        print(f"Verified Tools Directory: {tools_dir}")
        sys.exit(1)


class AIOrchestrator:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_root = os.path.abspath(os.path.join(self.base_dir, '..'))
        self.map_output_path = os.path.join(self.base_dir, 'repo_map.json')
        
    def initialize_task(self, jira_ticket_summary):
        print("=" * 60)
        print(f"🤖 INITIALIZING ORCHESTRATOR FOR TICKET: {jira_ticket_summary}")
        print("=" * 60)
        
        # 1. Just-in-Time (JIT) Map Refresh
        print("\n🔍 Step 1: Checking and refreshing repository map...")
        generate_repo_map(self.project_root, self.map_output_path)
        
        # 2. Load the Map for the Agent's Context
        with open(self.map_output_path, 'r', encoding='utf-8') as f:
            repo_map = json.load(f)
            
        print("✅ Repository map loaded into Agent memory.")
        return repo_map

    def agent_tool_read_file(self, relative_path):
        """The strict, secure tool exposed to the LLM to read files."""
        print(f"\n🛠️  [TOOL CALL]: Agent requested to read: {relative_path}")
        return secure_read_file(relative_path, self.project_root)

# --- Prototype Execution Simulation ---
if __name__ == "__main__":
    orchestrator = AIOrchestrator()
    ticket = "JIRA-404: Audit Terraform security groups and check user_data credentials"
    repo_tree = orchestrator.initialize_task(ticket)
    
    target_file = "git-driven-observability/terraform/security_test.tf"
    sanitized_content = orchestrator.agent_tool_read_file(target_file)
    
    print("\n--- [CONSTRUCTED LLM CONTEXT WINDOW] ---")
    print(f"Instructions based on ticket: {ticket}\n")
    print("Sanitized File Contents Provided to LLM:")
    print("-" * 40)
    print(sanitized_content)
    print("-" * 40)

    # =========================================================================
    # NEW: SIMULATING THE OUTBOUND GATEKEEPER
    # =========================================================================
    print("\n" + "="*60)
    print("🛡️  TESTING OUTBOUND GATEKEEPER LAYER")
    print("="*60)
    
    # Simulation 1: The AI generates a bad fix (hardcoding a new password)
    bad_ai_suggested_code = """
    resource "aws_instance" "fixed_bastion" {
      ami           = "ami-0c55b159cbfafe1f0"
      instance_type = "t3.medium"
      # I'm fixing this by resetting the admin password
      user_data = "echo 'admin:SaviProductionPassword2026!' | chpasswd"
    }
    """
    
    print("\n🔄 Scenario 1: AI attempts to submit code with a hardcoded password...")
    is_safe, reason = verify_clean_content(bad_ai_suggested_code)
    if not is_safe:
        print(f"❌ BLOCK COMMIT: {reason}")
    else:
        print("✅ Code approved for PR.")

    # Simulation 2: The AI generates a pristine fix using variables
    good_ai_suggested_code = """
    resource "aws_instance" "fixed_bastion" {
      ami           = "ami-0c55b159cbfafe1f0"
      instance_type = "t3.medium"
      user_data = var.bootstrap_script_path
    }
    """
    
    print("\n🔄 Scenario 2: AI attempts to submit clean, compliant code...")
    is_safe, reason = verify_clean_content(good_ai_suggested_code)
    if not is_safe:
        print(f"❌ BLOCK COMMIT: {reason}")
    else:
        print(f"✅ Code approved for PR! ({reason})")