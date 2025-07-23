import json
import os
from pathlib import Path
from typing import Dict, List, Set


class RepositoryAnalyzer:
    """Analyzes repository structure and detects frameworks/languages."""

    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()

    def analyze(self) -> Dict[str, any]:
        """Perform comprehensive repository analysis."""
        analysis = {
            "languages": self._detect_languages(),
            "frameworks": self._detect_frameworks(),
            "project_type": self._determine_project_type(),
            "structure": self._analyze_structure(),
            "dependencies": self._analyze_dependencies(),
            "config_files": self._find_config_files(),
            "entry_points": self._find_entry_points(),
        }

        return analysis

    def _detect_languages(self) -> Dict[str, int]:
        """Detect programming languages by file extensions."""
        language_map = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".jsx": "React",
            ".tsx": "React TypeScript",
            ".java": "Java",
            ".cpp": "C++",
            ".c": "C",
            ".h": "C/C++ Header",
            ".hpp": "C++ Header",
            ".rs": "Rust",
            ".go": "Go",
            ".php": "PHP",
            ".rb": "Ruby",
            ".swift": "Swift",
            ".kt": "Kotlin",
            ".scala": "Scala",
            ".cs": "C#",
            ".fs": "F#",
            ".sh": "Shell",
            ".bash": "Bash",
            ".zsh": "Zsh",
            ".ps1": "PowerShell",
            ".html": "HTML",
            ".css": "CSS",
            ".scss": "SCSS",
            ".sass": "Sass",
            ".less": "Less",
            ".sql": "SQL",
            ".r": "R",
            ".m": "MATLAB",
            ".dart": "Dart",
            ".elm": "Elm",
            ".clj": "Clojure",
            ".ex": "Elixir",
            ".erl": "Erlang",
            ".hs": "Haskell",
            ".ml": "OCaml",
            ".lua": "Lua",
            ".pl": "Perl",
            ".jl": "Julia",
        }

        language_counts = {}

        for file_path in self.repo_path.rglob("*"):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                if ext in language_map:
                    lang = language_map[ext]
                    language_counts[lang] = language_counts.get(lang, 0) + 1

        return dict(sorted(language_counts.items(), key=lambda x: x[1], reverse=True))

    def _detect_frameworks(self) -> List[str]:
        """Detect frameworks and libraries."""
        frameworks = set()

        # Check for package files
        package_indicators = {
            "package.json": self._analyze_package_json,
            "requirements.txt": self._analyze_requirements_txt,
            "Pipfile": self._analyze_pipfile,
            "pyproject.toml": self._analyze_pyproject_toml,
            "Cargo.toml": self._analyze_cargo_toml,
            "go.mod": self._analyze_go_mod,
            "pom.xml": self._analyze_pom_xml,
            "build.gradle": self._analyze_gradle,
            "composer.json": self._analyze_composer_json,
            "Gemfile": self._analyze_gemfile,
        }

        for filename, analyzer in package_indicators.items():
            file_path = self.repo_path / filename
            if file_path.exists():
                detected = analyzer(file_path)
                frameworks.update(detected)

        # Check for config files that indicate frameworks
        config_indicators = {
            "next.config.js": "Next.js",
            "nuxt.config.js": "Nuxt.js",
            "vue.config.js": "Vue.js",
            "angular.json": "Angular",
            "svelte.config.js": "Svelte",
            "gatsby-config.js": "Gatsby",
            "webpack.config.js": "Webpack",
            "vite.config.js": "Vite",
            "rollup.config.js": "Rollup",
            "docker-compose.yml": "Docker Compose",
            "Dockerfile": "Docker",
            "kubernetes.yaml": "Kubernetes",
            "terraform.tf": "Terraform",
            "ansible.yml": "Ansible",
        }

        for filename, framework in config_indicators.items():
            if (self.repo_path / filename).exists():
                frameworks.add(framework)

        return sorted(list(frameworks))

    def _analyze_package_json(self, file_path: Path) -> Set[str]:
        """Analyze package.json for frameworks."""
        frameworks = set()

        try:
            with open(file_path) as f:
                data = json.load(f)

            dependencies = data.get("dependencies", {})
            dev_dependencies = data.get("devDependencies", {})
            all_deps = {**dependencies, **dev_dependencies}

            framework_indicators = {
                "react": "React",
                "vue": "Vue.js",
                "angular": "Angular",
                "@angular/core": "Angular",
                "svelte": "Svelte",
                "next": "Next.js",
                "nuxt": "Nuxt.js",
                "gatsby": "Gatsby",
                "express": "Express.js",
                "fastify": "Fastify",
                "koa": "Koa.js",
                "nestjs": "NestJS",
                "@nestjs/core": "NestJS",
                "electron": "Electron",
                "ionic": "Ionic",
                "jest": "Jest",
                "mocha": "Mocha",
                "cypress": "Cypress",
                "playwright": "Playwright",
                "webpack": "Webpack",
                "vite": "Vite",
                "rollup": "Rollup",
                "parcel": "Parcel",
            }

            for dep, framework in framework_indicators.items():
                if any(dep in dep_name for dep_name in all_deps.keys()):
                    frameworks.add(framework)

        except (json.JSONDecodeError, FileNotFoundError):
            pass

        return frameworks

    def _analyze_requirements_txt(self, file_path: Path) -> Set[str]:
        """Analyze requirements.txt for Python frameworks."""
        frameworks = set()

        try:
            with open(file_path) as f:
                content = f.read().lower()

            framework_indicators = {
                "django": "Django",
                "flask": "Flask",
                "fastapi": "FastAPI",
                "tornado": "Tornado",
                "pyramid": "Pyramid",
                "bottle": "Bottle",
                "streamlit": "Streamlit",
                "dash": "Dash",
                "jupyterlab": "JupyterLab",
                "notebook": "Jupyter",
                "tensorflow": "TensorFlow",
                "pytorch": "PyTorch",
                "torch": "PyTorch",
                "scikit-learn": "Scikit-learn",
                "pandas": "Pandas",
                "numpy": "NumPy",
                "matplotlib": "Matplotlib",
                "seaborn": "Seaborn",
                "plotly": "Plotly",
                "celery": "Celery",
                "redis": "Redis",
                "sqlalchemy": "SQLAlchemy",
                "alembic": "Alembic",
                "pytest": "pytest",
                "black": "Black",
                "flake8": "Flake8",
                "mypy": "MyPy",
            }

            for indicator, framework in framework_indicators.items():
                if indicator in content:
                    frameworks.add(framework)

        except FileNotFoundError:
            pass

        return frameworks

    def _analyze_pipfile(self, file_path: Path) -> Set[str]:
        """Analyze Pipfile for Python frameworks."""
        # Similar to requirements.txt but with TOML parsing
        return self._analyze_requirements_txt(file_path)  # Simplified for now

    def _analyze_pyproject_toml(self, file_path: Path) -> Set[str]:
        """Analyze pyproject.toml for Python frameworks."""
        frameworks = set()

        try:
            with open(file_path) as f:
                content = f.read().lower()

            if "poetry" in content:
                frameworks.add("Poetry")
            if "setuptools" in content:
                frameworks.add("Setuptools")
            if "hatch" in content:
                frameworks.add("Hatch")

        except FileNotFoundError:
            pass

        return frameworks

    def _analyze_cargo_toml(self, file_path: Path) -> Set[str]:
        """Analyze Cargo.toml for Rust frameworks."""
        frameworks = {"Rust"}

        try:
            with open(file_path) as f:
                content = f.read().lower()

            if "tokio" in content:
                frameworks.add("Tokio")
            if "actix" in content:
                frameworks.add("Actix")
            if "rocket" in content:
                frameworks.add("Rocket")
            if "warp" in content:
                frameworks.add("Warp")

        except FileNotFoundError:
            pass

        return frameworks

    def _analyze_go_mod(self, file_path: Path) -> Set[str]:
        """Analyze go.mod for Go frameworks."""
        frameworks = {"Go"}

        try:
            with open(file_path) as f:
                content = f.read().lower()

            if "gin" in content:
                frameworks.add("Gin")
            if "echo" in content:
                frameworks.add("Echo")
            if "fiber" in content:
                frameworks.add("Fiber")

        except FileNotFoundError:
            pass

        return frameworks

    def _analyze_pom_xml(self, file_path: Path) -> Set[str]:
        """Analyze pom.xml for Java frameworks."""
        frameworks = {"Maven", "Java"}

        try:
            with open(file_path) as f:
                content = f.read().lower()

            if "spring" in content:
                frameworks.add("Spring")
            if "hibernate" in content:
                frameworks.add("Hibernate")
            if "junit" in content:
                frameworks.add("JUnit")

        except FileNotFoundError:
            pass

        return frameworks

    def _analyze_gradle(self, file_path: Path) -> Set[str]:
        """Analyze build.gradle for Java/Android frameworks."""
        frameworks = {"Gradle"}
        return frameworks

    def _analyze_composer_json(self, file_path: Path) -> Set[str]:
        """Analyze composer.json for PHP frameworks."""
        frameworks = {"Composer", "PHP"}

        try:
            with open(file_path) as f:
                data = json.load(f)

            dependencies = data.get("require", {})

            if "laravel/framework" in dependencies:
                frameworks.add("Laravel")
            if "symfony/symfony" in dependencies:
                frameworks.add("Symfony")

        except (json.JSONDecodeError, FileNotFoundError):
            pass

        return frameworks

    def _analyze_gemfile(self, file_path: Path) -> Set[str]:
        """Analyze Gemfile for Ruby frameworks."""
        frameworks = {"Ruby", "Bundler"}

        try:
            with open(file_path) as f:
                content = f.read().lower()

            if "rails" in content:
                frameworks.add("Ruby on Rails")
            if "sinatra" in content:
                frameworks.add("Sinatra")

        except FileNotFoundError:
            pass

        return frameworks

    def _determine_project_type(self) -> str:
        """Determine the primary project type."""

        # Check for specific indicators
        if (self.repo_path / "package.json").exists():
            return "Node.js/JavaScript"
        elif (self.repo_path / "requirements.txt").exists() or (
            self.repo_path / "pyproject.toml"
        ).exists():
            return "Python"
        elif (self.repo_path / "Cargo.toml").exists():
            return "Rust"
        elif (self.repo_path / "go.mod").exists():
            return "Go"
        elif (self.repo_path / "pom.xml").exists() or (
            self.repo_path / "build.gradle"
        ).exists():
            return "Java"
        elif (self.repo_path / "composer.json").exists():
            return "PHP"
        elif (self.repo_path / "Gemfile").exists():
            return "Ruby"
        elif (self.repo_path / "CMakeLists.txt").exists():
            return "C/C++"
        elif any((self.repo_path / f).exists() for f in ["Makefile", "makefile"]):
            return "C/C++/Generic"
        else:
            return "Unknown"

    def _analyze_structure(self) -> Dict[str, any]:
        """Analyze repository structure."""
        structure = {
            "total_files": 0,
            "total_directories": 0,
            "max_depth": 0,
            "common_directories": [],
        }

        common_dirs = set()
        max_depth = 0

        for root, dirs, files in os.walk(self.repo_path):
            depth = root.replace(str(self.repo_path), "").count(os.sep)
            max_depth = max(max_depth, depth)
            structure["total_files"] += len(files)
            structure["total_directories"] += len(dirs)

            # Track common directory names
            for d in dirs:
                if not d.startswith("."):
                    common_dirs.add(d)

        structure["max_depth"] = max_depth
        structure["common_directories"] = sorted(list(common_dirs))

        return structure

    def _analyze_dependencies(self) -> Dict[str, List[str]]:
        """Analyze project dependencies."""
        dependencies = {}

        # Package managers and their files
        dep_files = {
            "npm": "package.json",
            "pip": "requirements.txt",
            "poetry": "pyproject.toml",
            "cargo": "Cargo.toml",
            "go": "go.mod",
            "maven": "pom.xml",
            "gradle": "build.gradle",
            "composer": "composer.json",
            "bundler": "Gemfile",
        }

        for manager, filename in dep_files.items():
            file_path = self.repo_path / filename
            if file_path.exists():
                dependencies[manager] = [filename]

        return dependencies

    def _find_config_files(self) -> List[str]:
        """Find configuration files."""
        config_patterns = [
            "*.json",
            "*.yaml",
            "*.yml",
            "*.toml",
            "*.ini",
            "*.cfg",
            "*.conf",
            "*.config",
            "Dockerfile",
            "Makefile",
            ".env*",
        ]

        config_files = []

        for pattern in config_patterns:
            for file_path in self.repo_path.glob(pattern):
                if file_path.is_file():
                    config_files.append(file_path.name)

        return sorted(config_files)

    def _find_entry_points(self) -> List[str]:
        """Find likely entry points for the application."""
        entry_points = []

        common_entry_files = [
            "main.py",
            "app.py",
            "server.py",
            "index.js",
            "app.js",
            "main.js",
            "server.js",
            "index.html",
            "main.go",
            "main.rs",
            "Main.java",
            "index.php",
            "app.rb",
        ]

        for filename in common_entry_files:
            if (self.repo_path / filename).exists():
                entry_points.append(filename)

        return entry_points
