import os
import json
import hashlib

def get_dir_hash(root_dir, exclude_dirs, exclude_files):
    """Generates a quick hash of the directory structure to see if it changed."""
    hash_str = ""
    for root, dirs, files in os.walk(root_dir):
        # Apply our exclusion rules dynamically
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for f in sorted(files):
            if f not in exclude_files:
                hash_str += os.path.join(root, f)
    return hashlib.md5(hash_str.encode()).hexdigest()

def generate_repo_map(target_dir, output_file):
    # Ensure target_dir is absolutely resolved
    absolute_target = os.path.abspath(target_dir)
    
    exclude_dirs = {'.git', '__pycache__', 'node_modules', 'venv', '.ai-orchestrator', 'secrets'}
    exclude_files = {'.DS_Store', 'terraform.tfstate', '.env'}

    # 1. Check if we actually need to update
    current_hash = get_dir_hash(absolute_target, exclude_dirs, exclude_files)
    
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
        "project_name": os.path.basename(absolute_target),
        "structure_hash": current_hash,
        "map": build_tree(absolute_target)
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(repo_structure, f, indent=2)
    print(f"✅ Repo map updated for root: {absolute_target}. New hash: {current_hash}")

# This block ONLY runs when you manually execute this file from terminal
if __name__ == "__main__":
    # Get location of generate_map.py (C:\GitHub\ai-pr-orchestrator\.ai-orchestrator\tools)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Move up TWO levels to reach C:\GitHub\ai-pr-orchestrator
    true_project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
    
    # Place the map JSON inside .ai-orchestrator folder (one level up from here)
    map_destination = os.path.abspath(os.path.join(script_dir, '..', 'repo_map.json'))
    
    generate_repo_map(true_project_root, map_destination)