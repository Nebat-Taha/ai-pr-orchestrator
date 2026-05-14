# -----------------------------------------------------------------------------
# SERVICE: AI Persona & Context Orchestrator
#
# PURPOSE: This service manages the "System Prompts" that define the AI's 
#          expertise and constraints. It acts as a bridge between Jira metadata 
#          and the LLM's behavioral instructions.
#
# ARCHITECTURE: 
#   - File-Based Registry: Prompts are stored as markdown (.md) files in a 
#     central directory, allowing for easy updates without code changes.
#   - Dynamic Mapping: Inspects Jira labels to match specific infrastructure 
#     tasks with their corresponding expert persona (e.g., 'terraform' label 
#     loads 'terraform.md').
#
# LOGIC:
#   - Priority Routing: Iterates through ticket labels and breaks at the first 
#     valid match found in the filesystem.
#   - Fallback Mechanism: Provides a generic 'Senior DevOps' persona if no 
#     specific label matches are found, ensuring the pipeline never fails 
#     due to missing context.
#
# License: MIT License
# Copyright (c) 2026 Nebat Taha
# All rights reserved.
# -----------------------------------------------------------------------------
import os

class PromptService:
    def __init__(self, prompt_dir="prompts"):
        """
        Initializes the service and defines the source directory for prompt files.
        """
        self.prompt_dir = prompt_dir

    def get_context(self, labels):
        """
        Scans Jira labels and retrieves the matching system prompt from disk.
        
        Args:
            labels (list): A list of strings representing the Jira ticket labels.
            
        Returns:
            str: The raw text content of the system prompt to be sent to the LLM.
        """
        # Default fallback persona
        system_content = "You are a senior DevOps engineer."
        
        # Mapping Logic: Iterate through labels to find a corresponding .md file
        for label in labels:
            file_name = f"{label.lower()}.md"
            path = os.path.join(self.prompt_dir, file_name)
            
            # File I/O: Load matching expertise context
            if os.path.exists(path):
                with open(path, "r") as f:
                    system_content = f.read()
                print(f"🎯 Context Loaded: {file_name}")
                break # Priority: Stop at the first valid matching label found
        
        return system_content