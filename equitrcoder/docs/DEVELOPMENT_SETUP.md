# EQUITR Coder Development Setup Guide

Complete guide for developers who want to contribute to or extend EQUITR Coder.

## Prerequisites

- Python 3.8+
- Git
- Virtual environment tool (venv, conda, etc.)
- Code editor (VS Code, PyCharm, etc.)

## Development Installation

### 1. Clone the Repository

```bash
git clone https://github.com/equitr/EQUITR-coder.git
cd EQUITR-coder
```

### 2. Create Development Environment

```bash
# Create virtual environment
python -m venv equitr-dev
source equitr-dev/bin/activate  # On Windows: equitr-dev\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install development dependencies
pip install -r requirements-dev.txt

# Install in development mode
pip install -e .
```

### 3. Set Up Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Test hooks
pre-commit run --all-files
```

### 4. Configure Development Environment

```bash
# Set up development API key
export OPENAI_API_KEY="your-development-key"

# Create development config
mkdir -p ~/.equitr
cat > ~/.equitr/config-dev.yaml << EOF
llm:
  model: "gpt-4o-mini"
  temperature: 0.5
  budget: 5.0

orchestrator:
  use_multi_agent: false
  max_iterations: 10

git:
  auto_commit: false
EOF
```

## Project Structure

```
EQUITR-coder/
├── EQUITR_coder/              # Main package
│   ├── __init__.py
│   ├── interactive_cli.py     # Main CLI interface
│   ├── core/                  # Core modules
│   │   ├── orchestrator.py    # Main orchestration logic
│   │   ├── documentation.py   # Documentation generation
│   │   ├── supervisor.py      # Multi-agent coordination
│   │   ├── config.py          # Configuration management
│   │   └── session.py         # Session management
│   ├── providers/             # LLM providers
│   │   ├── openrouter.py      # OpenRouter provider
│   │   └── litellm.py         # LiteLLM provider
│   ├── programmatic/          # Programmatic API
│   │   ├── __init__.py
│   │   └── interface.py       # OOP interface
│   ├── tools/                 # Tool system
│   │   ├── __init__.py
│   │   ├── registry.py        # Tool registry
│   │   └── builtin/           # Built-in tools
│   └── ui/                    # User interface
│       ├── __init__.py
│       ├── tui.py             # Simple TUI
│       └── advanced_tui.py     # Advanced Textual TUI
├── tests/                     # Test suite
├── examples/                  # Usage examples
├── docs/                      # Documentation
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # Development dependencies
├── setup.py                   # Package setup
└── README.md                  # Project README
```

## Development Dependencies

Create `requirements-dev.txt`:

```txt
# Testing
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0

# Code Quality
black>=23.0.0
isort>=5.12.0
flake8>=6.0.0
mypy>=1.0.0

# Development Tools
pre-commit>=3.0.0
ipython>=8.0.0
jupyter>=1.0.0

# Documentation
sphinx>=5.0.0
sphinx-rtd-theme>=1.2.0

# Build Tools
build>=0.10.0
twine>=4.0.0
```

## Running Tests

### Unit Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=EQUITR_coder

# Run specific test file
pytest tests/test_orchestrator.py

# Run specific test
pytest tests/test_orchestrator.py::test_single_agent_mode
```

### Integration Tests

```bash
# Run integration tests (requires API key)
pytest tests/integration/

# Run with real API calls
EQUITR_INTEGRATION_TESTS=true pytest tests/integration/
```

### Test Configuration

Create `pytest.ini`:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --strict-markers
    --strict-config
    --verbose
    --tb=short
    --cov=EQUITR_coder
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
    --cov-fail-under=80
markers =
    slow: marks tests as slow (deselect with '-m "not slow"')
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

## Code Style and Formatting

### Black (Code Formatting)

```bash
# Format code
black EQUITR_coder/ tests/

# Check formatting
black --check EQUITR_coder/ tests/
```

### isort (Import Sorting)

```bash
# Sort imports
isort EQUITR_coder/ tests/

# Check sorting
isort --check-only EQUITR_coder/ tests/
```

### flake8 (Linting)

```bash
# Lint code
flake8 EQUITR_coder/ tests/
```

Create `.flake8`:

```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = 
    .git,
    __pycache__,
    build,
    dist,
    .eggs,
    *.egg-info,
    venv,
    env
```

### mypy (Type Checking)

```bash
# Type check
mypy EQUITR_coder/
```

Create `mypy.ini`:

```ini
[mypy]
python_version = 3.8
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True

[mypy-tests.*]
disallow_untyped_defs = False
```

## Pre-commit Configuration

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-json
      - id: check-toml

  - repo: https://github.com/psf/black
    rev: 23.1.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.0.1
    hooks:
      - id: mypy
```

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/new-feature
```

### 2. Implement Changes

```bash
# Make changes
vim EQUITR_coder/core/orchestrator.py

# Run tests
pytest tests/test_orchestrator.py

# Format code
black EQUITR_coder/
isort EQUITR_coder/
```

### 3. Test Changes

```bash
# Run full test suite
pytest

# Test with real CLI
equitrcoder --profile dev

# Test specific functionality
python -m pytest tests/test_interactive_cli.py -v
```

### 4. Commit Changes

```bash
# Stage changes
git add .

# Commit (pre-commit hooks will run)
git commit -m "feat: add new feature"

# Push branch
git push origin feature/new-feature
```

## Debugging

### Debug Mode

```bash
# Enable debug logging
export EQUITR_DEBUG=true
equitrcoder --profile dev

# Python debugging
python -m pdb -c continue -m EQUITR_coder.interactive_cli
```

### Debug Configuration

```yaml
# ~/.equitr/config-debug.yaml
llm:
  model: "gpt-4o-mini"
  temperature: 0.0
  budget: 1.0

orchestrator:
  use_multi_agent: false
  max_iterations: 3

debug:
  log_level: "DEBUG"
  save_conversations: true
  verbose_output: true
```

### Common Debug Commands

```bash
# Test specific components
python -c "from EQUITR_coder.core.orchestrator import AgentOrchestrator; print('OK')"

# Test configuration loading
python -c "from EQUITR_coder.core.config import config_manager; print(config_manager.load_config('dev'))"

# Test documentation generation
python -c "from EQUITR_coder.core.documentation import DocumentationGenerator; print('OK')"
```

## Adding New Features

### 1. Adding New Tools

```python
# EQUITR_coder/tools/builtin/my_tool.py
from typing import Type
from pydantic import BaseModel, Field
from ..base import Tool, ToolResult

class MyToolArgs(BaseModel):
    input_text: str = Field(..., description="Input text to process")

class MyTool(Tool):
    def get_name(self) -> str:
        return "my_tool"
    
    def get_description(self) -> str:
        return "Description of what my tool does"
    
    def get_args_schema(self) -> Type[BaseModel]:
        return MyToolArgs
    
    async def run(self, **kwargs) -> ToolResult:
        args = self.validate_args(kwargs)
        # Tool implementation
        return ToolResult(success=True, data={"result": "processed"})
```

### 2. Adding New Providers

```python
# EQUITR_coder/providers/my_provider.py
from typing import List, Optional
from .base import BaseProvider, Message, CompletionResponse

class MyProvider(BaseProvider):
    def __init__(self, api_key: str, base_url: str = "https://api.example.com"):
        self.api_key = api_key
        self.base_url = base_url
    
    async def create_completion(
        self,
        messages: List[Message],
        model: str = "default",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        **kwargs
    ) -> CompletionResponse:
        # Implementation
        pass
```

### 3. Adding Configuration Options

```python
# EQUITR_coder/core/config.py
@dataclass
class MyFeatureConfig:
    enabled: bool = True
    setting1: str = "default"
    setting2: int = 10

@dataclass
class Config:
    # ... existing fields ...
    my_feature: MyFeatureConfig = field(default_factory=MyFeatureConfig)
```

## Testing Guidelines

### Test Structure

```python
# tests/test_my_feature.py
import pytest
from unittest.mock import Mock, patch
from EQUITR_coder.core.my_feature import MyFeature

class TestMyFeature:
    @pytest.fixture
    def my_feature(self):
        return MyFeature()
    
    def test_basic_functionality(self, my_feature):
        result = my_feature.do_something()
        assert result == "expected"
    
    @pytest.mark.asyncio
    async def test_async_functionality(self, my_feature):
        result = await my_feature.do_something_async()
        assert result is not None
    
    @patch('EQUITR_coder.core.my_feature.external_api')
    def test_with_mock(self, mock_api, my_feature):
        mock_api.return_value = "mocked"
        result = my_feature.use_external_api()
        assert result == "mocked"
```

### Integration Tests

```python
# tests/integration/test_full_workflow.py
import pytest
from EQUITR_coder.interactive_cli import main

@pytest.mark.integration
@pytest.mark.asyncio
async def test_full_workflow():
    # Test complete workflow
    pass
```

## TUI Development

### Setting Up Textual Dev Tools
```bash
# Install Textual dev extras
pip install textual[dev]

# Run TUI in dev mode
textual run --dev equitrcoder.ui.advanced_tui:EquitrTUI

# Debug console
textual console  # In separate terminal
```

### Testing TUI Components
```python
# tests/test_tui.py
import pytest
from textual.app import App
from equitrcoder.ui.advanced_tui import EquitrTUI

class TestApp(App):
    def compose(self):
        yield Label("Test")

@pytest.mark.asyncio
async def test_tui():
    async with TestApp().run_test() as pilot:
        assert pilot.app is not None
```

### Mocking Models for TUI Tests
Use Litellm mocking:
```python
import litellm
litellm.set_verbose = True
litellm.success_callback = [lambda x: "Mock response"]
```

## Documentation

### Code Documentation

```python
def my_function(param1: str, param2: int) -> str:
    """
    Brief description of the function.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When param1 is invalid
    """
    pass
```

### API Documentation

```python
class MyClass:
    """
    Brief description of the class.
    
    This class handles...
    
    Attributes:
        attr1: Description of attr1
        attr2: Description of attr2
    
    Examples:
        >>> obj = MyClass()
        >>> result = obj.method()
        >>> print(result)
    """
```

## Performance Considerations

### Profiling

```bash
# Profile code
python -m cProfile -o profile.stats -m EQUITR_coder.interactive_cli

# Analyze profile
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"
```

### Memory Usage

```python
# Track memory usage
import tracemalloc

tracemalloc.start()
# Your code here
current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")
tracemalloc.stop()
```

## Release Process

### 1. Prepare Release

```bash
# Update version
vim setup.py  # Update version number

# Update changelog
vim CHANGELOG.md

# Run full tests
pytest

# Build package
python -m build
```

### 2. Release

```bash
# Tag release
git tag -a v0.2.0 -m "Release v0.2.0"
git push origin v0.2.0

# Upload to PyPI
python -m twine upload dist/*
```

## Contributing Guidelines

### Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Ensure all tests pass
5. Update documentation
6. Submit pull request

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests are included and pass
- [ ] Documentation is updated
- [ ] No breaking changes without discussion
- [ ] Performance impact considered
- [ ] Security implications reviewed

## Development Tools

### Recommended VS Code Extensions

- Python
- Black Formatter
- isort
- Pylance
- GitLens
- YAML

### Recommended Settings

```json
{
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.mypyEnabled": true,
    "editor.formatOnSave": true,
    "python.sortImports.args": ["--profile", "black"]
}
```

This development setup guide provides everything needed to contribute to EQUITR Coder effectively.