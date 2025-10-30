from pathlib import Path
from typing import Type, List, Dict, Any

from pydantic import BaseModel, Field

from ..base import Tool, ToolResult


class CreateFileArgs(BaseModel):
    path: str = Field(..., description="Relative file path to create")
    content: str = Field(..., description="Content to write to the file")


class CreateFile(Tool):
    def get_name(self) -> str:
        return "create_file"

    def get_description(self) -> str:
        return "Create a new file with given content"

    def get_args_schema(self) -> Type[BaseModel]:
        return CreateFileArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)

            # Resolve path relative to current working directory
            cwd = Path.cwd().resolve()
            file_path = (cwd / args.path).resolve()

            # Security check - prevent path traversal
            if not str(file_path).startswith(str(cwd)):
                return ToolResult(
                    success=False,
                    error="Path outside project directory is not allowed.",
                )

            # Create parent directories if they don't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content to file
            file_path.write_text(args.content, encoding="utf-8")

            return ToolResult(
                success=True,
                data={"path": str(file_path), "bytes_written": len(args.content)},
            )

        except Exception as e:
            return ToolResult(success=False, error=str(e))


class CreateFilesArgs(BaseModel):
    files: List[Dict[str, Any]] = Field(..., description="List of {path, content} entries to create atomically")


class CreateFiles(Tool):
    def get_name(self) -> str:
        return "create_files"

    def get_description(self) -> str:
        return "Create multiple files in a single operation (atomic best-effort)."

    def get_args_schema(self) -> Type[BaseModel]:
        return CreateFilesArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)
            cwd = Path.cwd().resolve()
            created: List[Dict[str, Any]] = []
            # First pass: validate all paths
            for item in args.files:
                rel = str(item.get("path", ""))
                file_path = (cwd / rel).resolve()
                if not str(file_path).startswith(str(cwd)):
                    return ToolResult(success=False, error=f"Path outside project directory: {rel}")
            # Second pass: create
            for item in args.files:
                rel = str(item.get("path", ""))
                content = str(item.get("content", ""))
                file_path = (cwd / rel).resolve()
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content, encoding="utf-8")
                created.append({"path": str(file_path), "bytes_written": len(content)})
            return ToolResult(success=True, data={"created": created, "count": len(created)})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ReadFileArgs(BaseModel):
    path: str = Field(..., description="Relative file path to read")


class ReadFile(Tool):
    def get_name(self) -> str:
        return "read_file"

    def get_description(self) -> str:
        return "Read the contents of a file"

    def get_args_schema(self) -> Type[BaseModel]:
        return ReadFileArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)

            cwd = Path.cwd().resolve()
            file_path = (cwd / args.path).resolve()

            # Security check
            if not str(file_path).startswith(str(cwd)):
                return ToolResult(
                    success=False,
                    error="Path outside project directory is not allowed.",
                )

            if not file_path.exists():
                return ToolResult(
                    success=False, error=f"File {file_path} does not exist"
                )

            content = file_path.read_text(encoding="utf-8")

            return ToolResult(
                success=True,
                data={"path": str(file_path), "content": content, "size": len(content)},
            )

        except Exception as e:
            return ToolResult(success=False, error=str(e))


class EditFileArgs(BaseModel):
    path: str = Field(..., description="Relative file path to edit")
    old_content: str = Field(..., description="Content to replace")
    new_content: str = Field(..., description="New content to insert")


class EditFile(Tool):
    def get_name(self) -> str:
        return "edit_file"

    def get_description(self) -> str:
        return "Edit a file by replacing old content with new content"

    def get_args_schema(self) -> Type[BaseModel]:
        return EditFileArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)

            cwd = Path.cwd().resolve()
            file_path = (cwd / args.path).resolve()

            # Security check
            if not str(file_path).startswith(str(cwd)):
                return ToolResult(
                    success=False,
                    error="Path outside project directory is not allowed.",
                )

            if not file_path.exists():
                return ToolResult(
                    success=False, error=f"File {file_path} does not exist"
                )

            content = file_path.read_text(encoding="utf-8")

            if args.old_content not in content:
                return ToolResult(success=False, error="Old content not found in file")

            new_content = content.replace(args.old_content, args.new_content)
            file_path.write_text(new_content, encoding="utf-8")

            return ToolResult(
                success=True,
                data={
                    "path": str(file_path),
                    "changes": 1,
                    "new_size": len(new_content),
                },
            )

        except Exception as e:
            return ToolResult(success=False, error=str(e))


class EditFilesArgs(BaseModel):
    edits: List[Dict[str, Any]] = Field(..., description="List of edits: {path, old_content, new_content}")


class EditFiles(Tool):
    def get_name(self) -> str:
        return "edit_files"

    def get_description(self) -> str:
        return "Apply multiple edits across files in one operation."

    def get_args_schema(self) -> Type[BaseModel]:
        return EditFilesArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)
            cwd = Path.cwd().resolve()
            changed: List[Dict[str, Any]] = []
            # Validate existence first
            for edit in args.edits:
                file_path = (cwd / str(edit.get("path", ""))).resolve()
                if not str(file_path).startswith(str(cwd)):
                    return ToolResult(success=False, error=f"Path outside project directory: {file_path}")
                if not file_path.exists():
                    return ToolResult(success=False, error=f"File {file_path} does not exist")
            # Apply edits
            for edit in args.edits:
                file_path = (cwd / str(edit.get("path", ""))).resolve()
                old_content = str(edit.get("old_content", ""))
                new_content = str(edit.get("new_content", ""))
                content = file_path.read_text(encoding="utf-8")
                if old_content not in content:
                    return ToolResult(success=False, error=f"Old content not found in {file_path}")
                updated = content.replace(old_content, new_content)
                file_path.write_text(updated, encoding="utf-8")
                changed.append({"path": str(file_path), "new_size": len(updated)})
            return ToolResult(success=True, data={"changed": changed, "count": len(changed)})
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class ListFilesArgs(BaseModel):
    path: str = Field(default=".", description="Directory path to list")


class ListFiles(Tool):
    def get_name(self) -> str:
        return "list_files"

    def get_description(self) -> str:
        return "List files and directories in a given path"

    def get_args_schema(self) -> Type[BaseModel]:
        return ListFilesArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)

            cwd = Path.cwd().resolve()
            dir_path = (cwd / args.path).resolve()

            # Security check
            if not str(dir_path).startswith(str(cwd)):
                return ToolResult(
                    success=False,
                    error="Path outside project directory is not allowed.",
                )

            if not dir_path.exists():
                return ToolResult(
                    success=False, error=f"Directory {dir_path} does not exist"
                )

            if not dir_path.is_dir():
                return ToolResult(success=False, error=f"{dir_path} is not a directory")

            files = []
            directories = []

            for item in dir_path.iterdir():
                if item.is_file():
                    files.append(
                        {"name": item.name, "size": item.stat().st_size, "type": "file"}
                    )
                elif item.is_dir():
                    directories.append({"name": item.name, "type": "directory"})

            return ToolResult(
                success=True,
                data={
                    "path": str(dir_path),
                    "files": files,
                    "directories": directories,
                    "total_items": len(files) + len(directories),
                },
            )

        except Exception as e:
            return ToolResult(success=False, error=str(e))
