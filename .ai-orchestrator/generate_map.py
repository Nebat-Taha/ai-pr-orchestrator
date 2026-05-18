import os
import json
import hashlib

def get_dir_hash(root_dir, exclude_dirs, exclude_files):
    """Generates a quick hash of the directory structure to see if it changed."""
    hash_str = ""
    for root, dirs, files in os.walk(root_dir):
        # Apply our exclusion rules
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for f in sorted(files):
            if f not in exclude_files:
                # We only care about paths and names, not content, for the Map
                hash_str += os.path.join(root, f)
    return hashlib.md5(hash_str.encode()).hexdigest()

def generate_repo_map(target_dir, output_file):
    exclude_dirs = {'.git', '__pycache__', 'node_modules', 'venv', '.ai-orchestrator', 'secrets'}
    exclude_files = {'.DS_Store', 'terraform.tfstate', '.env'}

    # 1. Check if we actually need to update
    current_hash = get_dir_hash(target_dir, exclude_dirs, exclude_files)
    
    # Check existing map hash
    if os.path.exists(output_file):
        with open(output_file, 'r') as f:
            try:
                old_data = json.load(f)
                if old_data.get("structure_hash") == current_hash:
                    print("⏩ No changes detected in repo structure. Skipping update.")
                    return
            except json.JSONDecodeError:
                pass

    def build_tree(current_path):
        tree = {}
        try:
            entries = sorted(os.scandir(current_path), key=lambda e: e.name)
            for entry in entries:
                if entry.is_dir() and entry.name not in exclude_dirs:
                    tree[entry.name] = build_tree(entry.path)
                elif entry.is_file() and entry.name not in exclude_files:
                    if '__files__' not in tree:
                        tree['__files__'] = []
                    tree['__files__'].append(entry.name)
        except PermissionError:
            pass
        return tree

    absolute_target = os.path.abspath(target_dir)
    repo_structure = {
        "project_name": os.path.basename(absolute_target),
        "structure_hash": current_hash, # 👈 The "Fingerprint" of the repo
        "map": build_tree(absolute_target)
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(repo_structure, f, indent=2)
    print(f"✅ Repo map updated. New hash: {current_hash}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(base_dir, '..')
    output_path = os.path.join(base_dir, 'repo_map.json')
    generate_repo_map(project_root, output_path)


    # The "Just-in-Time" (JIT) Approach (What we have now)
#In this scenario, you don't have a background service running. Instead, your Orchestrator (the main Python entry point) follows this sequence every time a Jira ticket is processed:

# 1. Ticket Received: Orchestrator wakes up.

# 2. Run generate_map.py: The Orchestrator calls the function we just wrote.

# 3. Hash Check: The script looks at the repo. If it sees the hash hasn't changed since the last ticket, it says "Nothing to do" and exits in milliseconds. If a file was added, it updates the JSON.

# 4. Start Agent: The Agent is handed the (now guaranteed to be fresh) repo_map.json.

# Advantage: Extremely simple. No extra processes to manage on your server.