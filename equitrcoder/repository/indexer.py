import os
from pathlib import Path
from typing import Dict, List

import pathspec

from .analyzer import RepositoryAnalyzer


class RepositoryIndexer:
    """Indexes repository files and provides context for the LLM."""

    def __init__(self, repo_path: str = ".", ignore_patterns: List[str] = None):
        self.repo_path = Path(repo_path).resolve()
        self.ignore_patterns = ignore_patterns or []
        self.analyzer = RepositoryAnalyzer(repo_path)

        # Default ignore patterns
        default_ignores = [
            ".git/**",
            "node_modules/**",
            "__pycache__/**",
            "*.pyc",
            ".venv/**",
            "venv/**",
            "env/**",
            ".env/**",
            "dist/**",
            "build/**",
            "target/**",
            "*.log",
            "*.tmp",
            "*.cache",
            ".DS_Store",
            "Thumbs.db",
        ]

        self.spec = pathspec.PathSpec.from_lines(
            "gitwildmatch", default_ignores + self.ignore_patterns
        )

    def should_ignore(self, path: Path) -> bool:
        """Check if a path should be ignored."""
        rel_path = path.relative_to(self.repo_path)
        return self.spec.match_file(str(rel_path))

    def get_file_tree(self) -> Dict:
        """Generate a file tree structure."""
        tree = {}

        for root, dirs, files in os.walk(self.repo_path):
            root_path = Path(root)

            # Filter out ignored directories
            dirs[:] = [d for d in dirs if not self.should_ignore(root_path / d)]

            rel_root = root_path.relative_to(self.repo_path)

            if rel_root == Path("."):
                current_level = tree
            else:
                # Navigate to the correct level in the tree
                current_level = tree
                for part in rel_root.parts:
                    current_level = current_level.setdefault(part, {})

            # Add files
            for file in files:
                file_path = root_path / file
                if not self.should_ignore(file_path):
                    current_level[file] = None  # None indicates it's a file

        return tree

    def get_important_files(self) -> List[str]:
        """Get a list of important files that should be prioritized."""
        important_patterns = [
            "README*",
            "readme*",
            "package.json",
            "requirements.txt",
            "pyproject.toml",
            "Cargo.toml",
            "go.mod",
            "pom.xml",
            "build.gradle",
            "Dockerfile",
            "docker-compose*",
            "Makefile",
            "makefile",
            "*.config.js",
            "*.config.ts",
            ".env*",
            "*.env",
            "main.*",
            "index.*",
            "app.*",
            "setup.py",
            "setup.cfg",
            "tox.ini",
            "pytest.ini",
            "jest.config.*",
            "webpack.config.*",
            "tsconfig.json",
            "jsconfig.json",
        ]

        important_files = []

        for pattern in important_patterns:
            for file_path in self.repo_path.glob(pattern):
                if file_path.is_file() and not self.should_ignore(file_path):
                    rel_path = file_path.relative_to(self.repo_path)
                    important_files.append(str(rel_path))

        return sorted(important_files)

    def get_file_summary(self, max_files: int = 50) -> List[Dict]:
        """Get a summary of files in the repository."""
        files_info = []
        count = 0

        for root, dirs, files in os.walk(self.repo_path):
            if count >= max_files:
                break

            root_path = Path(root)
            dirs[:] = [d for d in dirs if not self.should_ignore(root_path / d)]

            for file in files:
                if count >= max_files:
                    break

                file_path = root_path / file
                if not self.should_ignore(file_path):
                    rel_path = file_path.relative_to(self.repo_path)

                    try:
                        stat = file_path.stat()
                        files_info.append(
                            {
                                "path": str(rel_path),
                                "size": stat.st_size,
                                "extension": file_path.suffix,
                                "is_text": self._is_text_file(file_path),
                            }
                        )
                        count += 1
                    except (OSError, PermissionError):
                        continue

        return files_info

    def _is_text_file(self, file_path: Path) -> bool:
        """Check if a file is likely a text file."""
        text_extensions = {
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".html",
            ".css",
            ".scss",
            ".sass",
            ".less",
            ".json",
            ".yaml",
            ".yml",
            ".toml",
            ".ini",
            ".cfg",
            ".conf",
            ".txt",
            ".md",
            ".rst",
            ".tex",
            ".sh",
            ".bash",
            ".zsh",
            ".fish",
            ".ps1",
            ".bat",
            ".cmd",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".hpp",
            ".rs",
            ".go",
            ".php",
            ".rb",
            ".swift",
            ".kt",
            ".scala",
            ".cs",
            ".fs",
            ".hs",
            ".elm",
            ".clj",
            ".ex",
            ".erl",
            ".jl",
            ".r",
            ".m",
            ".sql",
            ".xml",
            ".svg",
            ".gitignore",
            ".dockerignore",
            ".env",
        }

        if file_path.suffix.lower() in text_extensions:
            return True

        # Check for files without extensions that are likely text
        if not file_path.suffix and file_path.name.lower() in {
            "readme",
            "license",
            "changelog",
            "makefile",
            "dockerfile",
            "vagrantfile",
            "rakefile",
            "gemfile",
            "procfile",
        }:
            return True

        # Try to read the first few bytes to check for binary content
        try:
            with open(file_path, "rb") as f:
                chunk = f.read(1024)
                if b"\x00" in chunk:  # Null bytes suggest binary
                    return False
                # Check if it's mostly printable ASCII
                try:
                    chunk.decode("utf-8")
                    return True
                except UnicodeDecodeError:
                    return False
        except (OSError, PermissionError):
            return False

    async def get_context(self, query: str = None) -> str:
        """Get repository context for the given query."""
        return await self.get_repository_context()

    async def get_repository_context(self) -> str:
        """Generate a comprehensive repository context for the LLM."""

        # Analyze repository
        analysis = self.analyzer.analyze()

        # Get file information
        file_tree = self.get_file_tree()
        important_files = self.get_important_files()
        self.get_file_summary()

        # Build context string
        context_parts = []

        # Project overview
        context_parts.append("# Repository Analysis")
        context_parts.append(f"Project Type: {analysis['project_type']}")

        if analysis["languages"]:
            languages = [
                f"{lang} ({count} files)"
                for lang, count in analysis["languages"].items()
            ]
            context_parts.append(f"Languages: {', '.join(languages[:5])}")  # Top 5

        if analysis["frameworks"]:
            context_parts.append(
                f"Frameworks: {', '.join(analysis['frameworks'][:10])}"
            )  # Top 10

        # Structure overview
        structure = analysis["structure"]
        context_parts.append(
            f"Structure: {structure['total_files']} files, {structure['total_directories']} directories"
        )

        # Important files
        if important_files:
            context_parts.append("\n## Important Files")
            for file in important_files[:20]:  # Top 20 important files
                context_parts.append(f"- {file}")

        # File tree (limited depth)
        context_parts.append("\n## File Tree")
        tree_str = self._format_tree(file_tree, max_depth=3)
        context_parts.append(tree_str)

        # Entry points
        if analysis["entry_points"]:
            context_parts.append("\n## Entry Points")
            for entry in analysis["entry_points"]:
                context_parts.append(f"- {entry}")

        # Configuration files
        if analysis["config_files"]:
            config_files = analysis["config_files"][:10]  # Top 10 config files
            context_parts.append("\n## Configuration Files")
            context_parts.append(f"{', '.join(config_files)}")

        return "\n".join(context_parts)

    def _format_tree(
        self, tree: Dict, prefix: str = "", max_depth: int = 3, current_depth: int = 0
    ) -> str:
        """Format file tree as a string with limited depth."""
        if current_depth >= max_depth:
            return ""

        lines = []
        items = sorted(tree.items())

        for i, (name, subtree) in enumerate(items):
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            lines.append(f"{prefix}{current_prefix}{name}")

            if subtree is not None:  # It's a directory
                extension = "    " if is_last else "│   "
                sublines = self._format_tree(
                    subtree, prefix + extension, max_depth, current_depth + 1
                )
                if sublines:
                    lines.append(sublines)

        return "\n".join(lines)
