# -----------------------------------------------------------------------------
# SERVICE: GitHub Integration & Version Control Management
#
# PURPOSE: This service manages all interactions with the GitHub API. It handles
#          branch creation, file persistence, and Pull Request (PR) orchestration.
#
# ARCHITECTURE: 
#   - PyGithub: Utilizes the official Python wrapper for the GitHub REST API.
#   - Git Flow: Implements a "Feature Branch" strategy where every Jira ticket 
#               results in a dedicated branch and isolated PR.
#   - Bot Identity: Implements 'InputGitAuthor' to clearly distinguish between 
#                   AI-generated commits and human developer contributions.
#
# LOGIC:
#   - Idempotent Branching: Checks for existing branches to prevent crash on retry.
#   - State Management: Uses file SHAs to determine if a file should be created 
#                       (POST) or updated (PUT) in the repository.
#
# License: MIT License
# Copyright (c) 2026 Nebat Taha
# All rights reserved.
# -----------------------------------------------------------------------------
import os
from github import Github, InputGitAuthor  # <--- Update this import
from dotenv import load_dotenv

load_dotenv()

class GitHubService:
    def __init__(self):
        """
        Initializes the GitHub client and validates repository connectivity.
        """
        token = os.getenv("GITHUB_TOKEN")
        repo_path = os.getenv("GITHUB_REPO")
        self.gh = Github(token)
        try:
            self.repo = self.gh.get_repo(repo_path)
        except Exception as e:
            print(f"❌ GitHub Init Error: {e}")
            self.repo = None

    def create_branch_and_pr(self, ticket_id, file_path, content, commit_message):
        """
        Orchestrates the full Git lifecycle for an AI-generated change:
        Branching -> File Creation/Update -> Pull Request.
        """
        if not self.repo:
            raise Exception("GitHub repository not initialized.")

        base_branch = "main"
        new_branch = f"feature/{ticket_id}"
        
        # Define the virtual identity for the AI bot to ensure clear audit trails
        bot_author = InputGitAuthor("AI-Orchestrator-Bot", "bot@devops-orchestrator.ai")

        # 1. BRANCHING: Get main SHA and create a new pointer (ref)
        sb = self.repo.get_branch(base_branch)
        try:
            self.repo.create_git_ref(ref=f"refs/heads/{new_branch}", sha=sb.commit.sha)
            print(f"Created branch: {new_branch}")
        except Exception:
            # Silence exception if branch already exists (supports idempotency)
            print(f"Branch {new_branch} already exists. Proceeding...")

        # 2. FILE PERSISTENCE: Handle both new files and existing file updates
        try:
            # Attempt to update existing file (requires current file SHA)
            contents = self.repo.get_contents(file_path, ref=new_branch)
            self.repo.update_file(
                path=file_path,
                message=commit_message,
                content=content,
                sha=contents.sha,
                branch=new_branch,
                author=bot_author,  # Attribution for the Git log
                committer=bot_author # Metadata for the Git log
            )
        except Exception:
            # Fallback: Create file if it does not exist in the target branch
            self.repo.create_file(
                path=file_path,
                message=commit_message,
                content=content,
                branch=new_branch,
                author=bot_author,  
                committer=bot_author
            )

        # 3. COLLABORATION: Open a PR for peer review or automated validation
        try:
            pr = self.repo.create_pull(
                title=f"[{ticket_id}] AI-Generated Infrastructure",
                body=f"This PR was automatically generated for Jira ticket {ticket_id}",
                head=new_branch,
                base=base_branch
            )
            return pr.html_url
        except Exception as e:
            # If PR is already open, find and return the existing URL
            if "A pull request already exists" in str(e):
                pulls = self.repo.get_pulls(state='open', head=f"{self.repo.owner.login}:{new_branch}")
                return pulls[0].html_url
            raise e