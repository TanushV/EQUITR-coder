# equitrcoder/utils/git_manager.py

import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any

# We need the TaskGroup type hint, but to avoid circular imports, we'll use a forward reference string
# or define a placeholder if necessary. A simple dict will suffice for type hinting here.
# from ..tools.builtin.todo import TaskGroup 

logger = logging.getLogger(__name__)

class GitManager:
    """Manages git operations for EQUITR Coder projects."""
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self.is_repo = self._check_is_repo()
    
    def _check_is_repo(self) -> bool:
        """Check if the path is a git repository."""
        return (self.repo_path / ".git").is_dir()
    
    def ensure_repo_is_ready(self):
        """Initializes a git repository if it doesn't exist."""
        if self.is_repo:
            return
        
        print("INFO: No git repository found. Initializing a new one.")
        try:
            subprocess.run(["git", "init"], cwd=self.repo_path, capture_output=True, text=True, encoding="utf-8", errors="ignore", check=True)
            self.is_repo = True
            self._create_gitignore()
            self.commit("feat: Initial commit by EQUITR Coder", auto_add=True)
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"WARNING: Could not initialize git repository: {e}")
            self.is_repo = False
    
    def _create_gitignore(self):
        """Create a default .gitignore file."""
        gitignore_content = """
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
.env
.venv
venv/
# IDEs & OS files
.vscode/
.idea/
.DS_Store
# EQUITR Coder session files
.EQUITR_todos_*.json
"""
        (self.repo_path / ".gitignore").write_text(gitignore_content.strip())
        print("INFO: Created .gitignore file.")
    
    def add_all(self) -> bool:
        """Add all changes to the staging area."""
        if not self.is_repo:
            return False
        try:
            subprocess.run(["git", "add", "-A"], cwd=self.repo_path, check=True, capture_output=True, text=True, encoding="utf-8", errors="ignore")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to `git add`: {e.stderr}")
            return False
    
    def commit(self, message: str, auto_add: bool = True) -> bool:
        """Commit changes with a specific message."""
        if not self.is_repo:
            return False
        
        if auto_add:
            self.add_all()
        
        # Check if there are changes to commit
        status_result = subprocess.run(["git", "status", "--porcelain"], cwd=self.repo_path, capture_output=True, text=True, encoding="utf-8", errors="ignore")
        if not status_result.stdout.strip():
            logger.info("No changes to commit.")
            return True # Nothing to do, so it's a "success"
        
        try:
            subprocess.run(["git", "commit", "-m", message], cwd=self.repo_path, check=True, capture_output=True, text=True, encoding="utf-8", errors="ignore")
            logger.info(f"Committed changes with message: {message}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to commit: {e.stderr}")
            return False
    
    def commit_task_group_completion(self, group: Dict[str, Any]) -> bool:
        """Create a descriptive commit after a task group is completed."""
        specialization = group.get('specialization', 'general')
        group_id = group.get('group_id', 'untitled_group')
        description = group.get('description', 'Completed a task group.')
        
        # Using conventional commit format for clarity
        commit_message = f"feat({specialization}): Complete task group '{group_id}'\n\n{description}"
        
        print(f"📝 Preparing to commit for completed group: {group_id}")
        return self.commit(commit_message, auto_add=True)
    
    def commit_phase_completion(self, phase_num: int, completed_groups: List[Dict[str, Any]]) -> bool:
        """Create a descriptive commit after a phase of task groups is completed."""
        group_details = []
        for group in completed_groups:
            group_id = group.get('group_id', 'untitled')
            specialization = group.get('specialization', 'general')
            group_details.append(f"- {group_id} ({specialization})")
        
        commit_message = f"chore(orchestration): Complete Phase {phase_num}\n\nCompleted the following task groups:\n" + "\n".join(group_details)
        
        print(f"📝 Preparing to commit for completed phase: {phase_num}")
        return self.commit(commit_message, auto_add=True)

def create_git_manager(repo_path: str = ".") -> GitManager:
    """Factory function to create a GitManager instance."""
    return GitManager(repo_path)