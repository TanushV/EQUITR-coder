import os
from typing import Type

import git
from pydantic import BaseModel, Field

from ..base import Tool, ToolResult


class GitCommitArgs(BaseModel):
    message: str = Field(..., description="Commit message")
    add_all: bool = Field(
        default=True, description="Whether to add all changes before committing"
    )


class GitCommit(Tool):
    def get_name(self) -> str:
        return "git_commit"

    def get_description(self) -> str:
        return "Stage changes and create a git commit"

    def get_args_schema(self) -> Type[BaseModel]:
        return GitCommitArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)
            repo = self._get_repository()
            
            if args.add_all:
                repo.git.add(all=True)
            
            if not self._has_changes_to_commit(repo):
                return ToolResult(success=False, error="No changes to commit")
            
            commit = repo.index.commit(args.message)
            return self._create_commit_result(commit, args.message)

        except git.InvalidGitRepositoryError:
            return ToolResult(success=False, error="Not in a git repository")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _get_repository(self):
        """Get the git repository for the current directory"""
        return git.Repo(os.getcwd())
    
    def _has_changes_to_commit(self, repo) -> bool:
        """Check if there are any changes to commit"""
        return bool(repo.index.diff("HEAD"))
    
    def _create_commit_result(self, commit, message):
        """Create the result data for a successful commit"""
        return ToolResult(
            success=True,
            data={
                "commit_hash": commit.hexsha,
                "message": message,
                "author": str(commit.author),
                "files_changed": len(commit.stats.files),
            },
        )


class GitStatusArgs(BaseModel):
    pass


class GitStatus(Tool):
    def get_name(self) -> str:
        return "git_status"

    def get_description(self) -> str:
        return "Get the current git repository status"

    def get_args_schema(self) -> Type[BaseModel]:
        return GitStatusArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            repo = self._get_repository()
            status_data = self._get_status_data(repo)
            return ToolResult(success=True, data=status_data)

        except git.InvalidGitRepositoryError:
            return ToolResult(success=False, error="Not in a git repository")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _get_repository(self):
        """Get the git repository for the current directory"""
        return git.Repo(os.getcwd())
    
    def _get_status_data(self, repo):
        """Get comprehensive status information from the repository"""
        untracked_files = repo.untracked_files
        modified_files = [item.a_path for item in repo.index.diff(None)]
        staged_files = [item.a_path for item in repo.index.diff("HEAD")]
        current_branch = repo.active_branch.name if repo.active_branch else "HEAD"
        
        is_clean = (len(untracked_files) == 0 and 
                   len(modified_files) == 0 and 
                   len(staged_files) == 0)
        
        return {
            "current_branch": current_branch,
            "untracked_files": untracked_files,
            "modified_files": modified_files,
            "staged_files": staged_files,
            "clean": is_clean,
        }


class GitDiffArgs(BaseModel):
    file_path: str = Field(default="", description="Specific file to diff (optional)")
    staged: bool = Field(
        default=False,
        description="Show staged changes instead of working directory changes",
    )


class GitDiff(Tool):
    def get_name(self) -> str:
        return "git_diff"

    def get_description(self) -> str:
        return "Show git diff for changes"

    def get_args_schema(self) -> Type[BaseModel]:
        return GitDiffArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)
            repo = self._get_repository()
            diff = self._get_diff(repo, args.staged)
            diff_data = self._process_diff(diff, args.file_path, args.staged)
            
            return ToolResult(success=True, data=diff_data)

        except git.InvalidGitRepositoryError:
            return ToolResult(success=False, error="Not in a git repository")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
    
    def _get_repository(self):
        """Get the git repository for the current directory"""
        return git.Repo(os.getcwd())
    
    def _get_diff(self, repo, staged: bool):
        """Get the appropriate diff based on staged flag"""
        if staged:
            return repo.index.diff("HEAD")  # Show staged changes
        else:
            return repo.index.diff(None)    # Show working directory changes
    
    def _process_diff(self, diff, file_path_filter: str, staged: bool):
        """Process diff items and generate diff text"""
        diff_text = ""
        files_changed = []
        
        for item in diff:
            file_path = item.a_path or item.b_path
            
            if file_path_filter and file_path != file_path_filter:
                continue
            
            files_changed.append(file_path)
            
            if hasattr(item, "diff") and item.diff:
                diff_text += f"\n--- a/{file_path}\n+++ b/{file_path}\n"
                diff_text += item.diff.decode("utf-8", errors="replace")
        
        return {
            "diff": diff_text,
            "files_changed": files_changed,
            "staged": staged,
        }
