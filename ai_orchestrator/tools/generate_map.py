"""
AI-Orchestrator: Repository Mapper
Description: Generates a JSON project map. Uses 'repo_config.json' to determine 
             which directories and files to ignore.
License: MIT License
Copyright (c) 2026 Nebat Taha / Savi Finance
"""
import os
import json
import hashlib

def load_repo_config():
    """
    Loads exclusion rules from inside the .ai-orchestrator module.
    This ensures portability when merging with other repositories.
    """
    # 1. Get current script directory (tools/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Get the parent directory (.ai-orchestrator/)
    module_dir = os.path.dirname(script_dir)
    
    # 3. Look for config inside the module
    config_path = os.path.join(module_dir, 'repo_config.json')
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"❌ Critical Configuration Error: 'repo_config.json' not found at expected location: {config_path}. "
            "Ensure the config file is inside the .ai-orchestrator folder."
        )
        
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)
def get_dir_hash(root_dir, exclude_dirs, exclude_files):
    """Generates a hash of the directory structure."""
    hash_str = ""
    for root, dirs, files in os.walk(root_dir):
        # Apply our exclusion rules dynamically
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for f in sorted(files):
            if f not in exclude_files:
                hash_str += os.path.join(root, f)
    return hashlib.md5(hash_str.encode()).hexdigest()

def generate_repo_map(target_dir, output_file):
    print(f"DEBUG: Scanning root path: {target_dir}")
    config = load_repo_config()
    exclude_dirs = set(config.get("exclude_dirs", []))
    exclude_files = set(config.get("exclude_files", []))

    # Calculate hash using the target_dir passed to the function
    current_hash = get_dir_hash(target_dir, exclude_dirs, exclude_files)
    
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
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
                # print(f"DEBUG: Checking entry: {entry.name} | Is Dir: {entry.is_dir()} | Excluded: {entry.name in exclude_dirs}")
                if entry.is_dir() and entry.name not in exclude_dirs:
                    tree[entry.name] = build_tree(entry.path)
                elif entry.is_file() and entry.name not in exclude_files:
                    if '__files__' not in tree:
                        tree['__files__'] = []
                    tree['__files__'].append(entry.name)
        except PermissionError:
            pass
        return tree

    repo_structure = {
        "project_name": os.path.basename(target_dir),
        "structure_hash": current_hash,
        "map": build_tree(target_dir)
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(repo_structure, f, indent=2)
    print(f"✅ Repo map updated for root: {target_dir}. New hash: {current_hash}")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Assuming tools are in .ai-orchestrator/tools/
    true_project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
    map_destination = os.path.abspath(os.path.join(script_dir, '..', 'repo_map.json'))
    
    generate_repo_map(true_project_root, map_destination)