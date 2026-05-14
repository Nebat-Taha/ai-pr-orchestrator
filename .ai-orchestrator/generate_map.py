import os
import json

def generate_repo_map(target_dir, output_file):
    # 1. Define the 'Blocked' zones
    exclude_dirs = {
        '.git', '__pycache__', 'node_modules', 'venv', 
        '.env', 'secrets', 'certs', 
        '.ai-orchestrator' # 👈 IMPORTANT: The bot shouldn't map its own logic
    }
    exclude_files = {
        '.DS_Store', 'package-lock.json', 'terraform.tfstate', '.env'
    }

    def build_tree(current_path):
        tree = {}
        try:
            for entry in os.scandir(current_path):
                if entry.is_dir():
                    if entry.name not in exclude_dirs:
                        tree[entry.name] = build_tree(entry.path)
                elif entry.is_file():
                    if entry.name not in exclude_files:
                        if '__files__' not in tree:
                            tree['__files__'] = []
                        tree['__files__'].append(entry.name)
        except PermissionError:
            pass
        return tree

    # Determine absolute path of the target (the root of the whole repo)
    absolute_target = os.path.abspath(target_dir)
    
    repo_structure = {
        "project_name": os.path.basename(absolute_target),
        "root_path": absolute_target, # Helpful for the orchestrator later
        "map": build_tree(absolute_target)
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(repo_structure, f, indent=2)

    print(f"✅ Success! Repo map of [{os.path.basename(absolute_target)}] generated at: {output_file}")

if __name__ == "__main__":
    # Path logic: '..' moves up from .ai-orchestrator/ to the root of the repo
    # Path logic: os.path.join helps keep it OS-agnostic
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(base_dir, '..')
    
    # We save the JSON inside our own folder so it's ready for the Agent
    output_path = os.path.join(base_dir, 'repo_map.json')
    
    generate_repo_map(target_dir=project_root, output_file=output_path)