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

            try:
                repo = git.Repo(os.getcwd())
            except git.InvalidGitRepositoryError:
                return ToolResult(success=False, error="Not in a git repository")

            if args.add_all:
                repo.git.add(all=True)

            # Check if there are any changes to commit
            if not repo.index.diff("HEAD"):
                return ToolResult(success=False, error="No changes to commit")

            commit = repo.index.commit(args.message)

            return ToolResult(
                success=True,
                data={
                    "commit_hash": commit.hexsha,
                    "message": args.message,
                    "author": str(commit.author),
                    "files_changed": len(commit.stats.files),
                },
            )

        except Exception as e:
            return ToolResult(success=False, error=str(e))


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
            try:
                repo = git.Repo(os.getcwd())
            except git.InvalidGitRepositoryError:
                return ToolResult(success=False, error="Not in a git repository")

            # Get status information
            untracked_files = repo.untracked_files
            modified_files = [item.a_path for item in repo.index.diff(None)]
            staged_files = [item.a_path for item in repo.index.diff("HEAD")]

            current_branch = repo.active_branch.name if repo.active_branch else "HEAD"

            return ToolResult(
                success=True,
                data={
                    "current_branch": current_branch,
                    "untracked_files": untracked_files,
                    "modified_files": modified_files,
                    "staged_files": staged_files,
                    "clean": len(untracked_files) == 0
                    and len(modified_files) == 0
                    and len(staged_files) == 0,
                },
            )

        except Exception as e:
            return ToolResult(success=False, error=str(e))


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

            try:
                repo = git.Repo(os.getcwd())
            except git.InvalidGitRepositoryError:
                return ToolResult(success=False, error="Not in a git repository")

            if args.staged:
                # Show staged changes
                diff = repo.index.diff("HEAD")
            else:
                # Show working directory changes
                diff = repo.index.diff(None)

            diff_text = ""
            files_changed = []

            for item in diff:
                file_path = item.a_path or item.b_path
                if args.file_path and file_path != args.file_path:
                    continue

                files_changed.append(file_path)

                if hasattr(item, "diff") and item.diff:
                    diff_text += f"\n--- a/{file_path}\n+++ b/{file_path}\n"
                    diff_text += item.diff.decode("utf-8", errors="replace")

            return ToolResult(
                success=True,
                data={
                    "diff": diff_text,
                    "files_changed": files_changed,
                    "staged": args.staged,
                },
            )

        except Exception as e:
            return ToolResult(success=False, error=str(e))
