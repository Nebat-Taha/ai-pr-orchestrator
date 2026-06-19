import os

class PersonaConfigurationError(Exception):
    """Raised when an AI orchestration persona template cannot be resolved or safely loaded."""
    pass

class PromptService:
    def __init__(self):
        pass

    def get_context(self, labels: list, base_path: str, profile_filename: str = None) -> str:
        """
        Dynamically extracts system persona configuration matrices.
        Enforces strict fail-fast validation: resolves explicitly via profile_filename 
        or falls back to explicit label inference if the orchestrator fails to route it.and couples them 
        with the global platform standards matrix.
        """
        target_file = None

        # 1. Resolve target file name (Prioritize dynamic registration, fallback to explicit matching)
        if profile_filename:
            target_file = profile_filename
        elif labels:
            # Normalize labels to lowercase for resilient checking
            normalized_labels = [str(label).lower() for label in labels]
            for label in normalized_labels:
                if label in ["ansible", "yaml"]:
                    target_file = "ansible.md"
                    break
                elif label in ["python", "script"]:
                    target_file = "python.md"
                    break
                elif label in ["terraform", "hcl", "iac"]:
                    target_file = "terraform.md"
                    break

        # 2. Halt immediately if no logical blueprint target could be deduced
        if not target_file:
            raise PersonaConfigurationError(
                f"Orchestration Routing Failed: No explicit profile_filename provided, "
                f"and labels {labels} could not be automatically mapped to a known engineering persona."
            )

        # 3. Build path and strictly validate file presence on disk
        full_prompt_path = os.path.normpath(os.path.join(base_path, target_file))
        standards_path = os.path.normpath(os.path.join(base_path, "standards.md"))
        print(f"📖 Attempting to load prompt profile matrix from: {full_prompt_path}")

        if not os.path.exists(full_prompt_path):
            raise PersonaConfigurationError(
                f"Infrastructure Blueprint Missing: Resolved target file '{target_file}' "
                f"but it does not exist at path: {full_prompt_path}. "
                f"An engineer must define this markdown template in the workspace."
            )

        # 4. Read content securely—no hidden fallback to generic default strings
        try:
            # Load the language-specific instruction rules
            with open(full_prompt_path, 'r', encoding='utf-8') as f:
                persona_content = f.read().strip()
            
            # Load the global engineering repository standards if present
            standards_content = ""
            if os.path.exists(standards_path):
                with open(standards_path, 'r', encoding='utf-8') as f:
                    standards_content = f.read().strip()

            # Merge the knowledge bases natively so the model sees both layers
            combined_context = f"{standards_content}\n\n{persona_content}"
            return combined_context

        except Exception as e:
            raise PersonaConfigurationError(f"Failed to compile system prompt context. Reason: {e}")