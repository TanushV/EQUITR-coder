# Adding Custom Tools Guide

This guide explains how to create and add custom tools to EQUITR Coder. Custom tools extend agent capabilities with specialized functionality for different domains.

## Overview

EQUITR Coder has three types of tools:
- **Builtin Tools**: Core functionality (file operations, git, shell, etc.)
- **Custom Tools**: Domain-specific tools (testing, deployment, etc.)
- **MCP Tools**: External tools via Model Context Protocol

Custom tools are automatically discovered and made available to agents based on their profiles.

### MCP Tools via JSON-configured servers

You can add external MCP servers without writing Python code by adding them to the MCP JSON config (see MCP Integration Guide). Each server becomes a tool `mcp:<serverName>` that forwards calls to the server's tools.


---

## 1. Tool Structure

### Basic Tool Template

```python
# equitrcoder/tools/custom/my_tools.py

from typing import Type
from pydantic import BaseModel, Field
from ..base import Tool, ToolResult

class MyToolArgs(BaseModel):
    """Arguments schema for the tool."""
    param1: str = Field(..., description="Required parameter description")
    param2: int = Field(default=10, description="Optional parameter with default")
    param3: bool = Field(default=False, description="Boolean parameter")

class MyTool(Tool):
    def get_name(self) -> str:
        return "my_tool"

    def get_description(self) -> str:
        return "Brief description of what this tool does"

    def get_args_schema(self) -> Type[BaseModel]:
        return MyToolArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            # Validate arguments
            args = self.validate_args(kwargs)
            
            # Implement tool logic here
            result = f"Tool executed with {args.param1}"
            
            return ToolResult(
                success=True,
                data={
                    "result": result,
                    "param1": args.param1,
                    "param2": args.param2
                }
            )
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))
```

### Key Components

1. **Arguments Schema**: Pydantic model defining tool parameters
2. **Tool Class**: Inherits from `Tool` base class
3. **Required Methods**:
   - `get_name()`: Unique tool identifier
   - `get_description()`: Human-readable description
   - `get_args_schema()`: Returns the arguments schema
   - `run()`: Async method that executes the tool logic

---

## 2. Tool Categories & Examples

### Testing Tools

```python
# equitrcoder/tools/custom/testing_tools.py

class RunTests(Tool):
    def get_name(self) -> str:
        return "run_tests"
    
    def get_description(self) -> str:
        return "Run Python tests using pytest with configurable options"
    
    # Implementation handles pytest execution, result parsing, etc.
```

**Use Cases**: Unit testing, integration testing, test coverage analysis

### Backend Tools

```python
# equitrcoder/tools/custom/backend_tools.py

class ApiTest(Tool):
    def get_name(self) -> str:
        return "api_test"
    
    def get_description(self) -> str:
        return "Test API endpoints with various HTTP methods"
    
    # Implementation handles HTTP requests, response validation, etc.
```

**Use Cases**: API testing, database operations, server management

### Frontend Tools

```python
# equitrcoder/tools/custom/frontend_tools.py

class BuildProject(Tool):
    def get_name(self) -> str:
        return "build_project"
    
    def get_description(self) -> str:
        return "Build a frontend project using npm, yarn, or other build tools"
    
    # Implementation handles build processes, asset optimization, etc.
```

**Use Cases**: Project building, dependency management, HTML validation

### DevOps Tools

```python
# equitrcoder/tools/custom/devops_tools.py

class DockerBuild(Tool):
    def get_name(self) -> str:
        return "docker_build"
    
    def get_description(self) -> str:
        return "Build Docker images from Dockerfiles"
    
    # Implementation handles Docker operations, manifest generation, etc.
```

**Use Cases**: Containerization, deployment, infrastructure management

---

## 3. Best Practices

### Error Handling

```python
async def run(self, **kwargs) -> ToolResult:
    try:
        args = self.validate_args(kwargs)
        
        # Your tool logic here
        result = perform_operation(args)
        
        return ToolResult(success=True, data=result)
        
    except ValidationError as e:
        return ToolResult(success=False, error=f"Invalid arguments: {e}")
    except subprocess.TimeoutExpired:
        return ToolResult(success=False, error="Operation timed out")
    except FileNotFoundError as e:
        return ToolResult(success=False, error=f"Required file not found: {e}")
    except Exception as e:
        return ToolResult(success=False, error=str(e))
```

### Subprocess Operations

```python
import subprocess

async def run(self, **kwargs) -> ToolResult:
    try:
        args = self.validate_args(kwargs)
        
        # Run external command
        result = subprocess.run(
            ["command", "arg1", "arg2"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        return ToolResult(
            success=result.returncode == 0,
            data={
                "stdout": result.stdout,
                "stderr": result.stderr,
                "return_code": result.returncode
            },
            error=result.stderr if result.returncode != 0 else None
        )
        
    except subprocess.TimeoutExpired:
        return ToolResult(success=False, error="Command timed out")
```

### File Operations

```python
from pathlib import Path

async def run(self, **kwargs) -> ToolResult:
    try:
        args = self.validate_args(kwargs)
        
        file_path = Path(args.file_path)
        
        # Security check
        if not file_path.exists():
            return ToolResult(success=False, error=f"File not found: {args.file_path}")
        
        # Read/write operations
        content = file_path.read_text(encoding='utf-8')
        
        return ToolResult(
            success=True,
            data={
                "content": content,
                "size": len(content),
                "path": str(file_path)
            }
        )
        
    except Exception as e:
        return ToolResult(success=False, error=str(e))
```

---

## 4. Adding Tools to Profiles

### Update Profile Configuration

```yaml
# equitrcoder/profiles/my_profile.yaml

name: "MySpecialist"
description: "A specialist with custom tools"

system_prompt: |
  You are a specialist with access to custom tools...

# Add your custom tools here
allowed_tools:
  - my_tool
  - another_custom_tool
```

### Profile-Tool Mapping

| Profile | Recommended Tools |
|---------|------------------|
| `qa_engineer` | `run_tests`, `test_coverage`, `lint_code` |
| `backend_dev` | `api_test`, `database_query`, `start_server` |
| `frontend_dev` | `build_project`, `serve_dev`, `install_dependencies` |
| `devops` | `docker_build`, `create_dockerfile`, `generate_k8s_manifest` |

---

## 5. Tool Discovery

Tools are automatically discovered when placed in the `equitrcoder/tools/custom/` directory.

### Discovery Process

1. **File Scanning**: Discovery system scans `custom/` directory
2. **Class Detection**: Finds classes inheriting from `Tool`
3. **Registration**: Instantiates and registers tools
4. **Availability**: Tools become available to agents

### Verification

```python
# Test tool discovery
from equitrcoder.tools.discovery import discover_tools

tools = discover_tools()
tool_names = [tool.get_name() for tool in tools]
print("Available tools:", tool_names)
```

---

## 6. Advanced Features

### Conditional Tool Loading

```python
class ConditionalTool(Tool):
    def __init__(self):
        super().__init__()
        # Check if required dependencies are available
        try:
            import required_package
            self.available = True
        except ImportError:
            self.available = False
    
    async def run(self, **kwargs) -> ToolResult:
        if not self.available:
            return ToolResult(
                success=False, 
                error="Required dependencies not installed"
            )
        # Tool logic here
```

### Tool Configuration

```python
class ConfigurableTool(Tool):
    def __init__(self, config_path: str = "tool_config.yaml"):
        super().__init__()
        self.config = self._load_config(config_path)
    
    def _load_config(self, path: str) -> dict:
        # Load tool-specific configuration
        pass
```

### Async Operations

```python
import asyncio
import aiohttp

class AsyncTool(Tool):
    async def run(self, **kwargs) -> ToolResult:
        args = self.validate_args(kwargs)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(args.url) as response:
                data = await response.json()
                
        return ToolResult(success=True, data=data)
```

---

## 7. Testing Custom Tools

### Unit Tests

```python
# tests/test_custom_tools.py

import pytest
from equitrcoder.tools.custom.my_tools import MyTool

@pytest.mark.asyncio
async def test_my_tool():
    tool = MyTool()
    
    result = await tool.run(
        param1="test_value",
        param2=42
    )
    
    assert result.success
    assert result.data["param1"] == "test_value"
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_tool_in_agent():
    from equitrcoder.core.profile_manager import ProfileManager
    
    pm = ProfileManager()
    config = pm.get_agent_config("my_profile")
    
    assert "my_tool" in config["allowed_tools"]
```

---

## 8. Common Patterns

### Command-Line Tools

```python
class CliTool(Tool):
    async def run(self, **kwargs) -> ToolResult:
        args = self.validate_args(kwargs)
        
        cmd = ["cli_command"] + args.arguments
        
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=args.timeout
        )
        
        return ToolResult(
            success=result.returncode == 0,
            data={"output": result.stdout},
            error=result.stderr if result.returncode != 0 else None
        )
```

### HTTP API Tools

```python
class ApiTool(Tool):
    async def run(self, **kwargs) -> ToolResult:
        args = self.validate_args(kwargs)
        
        response = requests.post(
            args.endpoint,
            json=args.payload,
            headers=args.headers,
            timeout=args.timeout
        )
        
        return ToolResult(
            success=response.status_code < 400,
            data=response.json(),
            error=f"HTTP {response.status_code}" if response.status_code >= 400 else None
        )
```

### File Processing Tools

```python
class FileProcessorTool(Tool):
    async def run(self, **kwargs) -> ToolResult:
        args = self.validate_args(kwargs)
        
        input_path = Path(args.input_file)
        output_path = Path(args.output_file)
        
        # Process file
        processed_content = self._process_file(input_path.read_text())
        output_path.write_text(processed_content)
        
        return ToolResult(
            success=True,
            data={
                "input_file": str(input_path),
                "output_file": str(output_path),
                "size": len(processed_content)
            }
        )
```

---

## 9. Troubleshooting

### Common Issues

1. **Tool Not Discovered**
   - Check file is in `equitrcoder/tools/custom/`
   - Ensure class inherits from `Tool`
   - Verify no syntax errors

2. **Import Errors**
   - Check all imports are available
   - Use conditional imports for optional dependencies

3. **Validation Errors**
   - Ensure `get_args_schema()` returns correct Pydantic model
   - Check field types and constraints

### Debugging

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test tool directly
tool = MyTool()
result = await tool.run(param1="test")
print(result)
```

---

## 10. Contributing Tools

### Guidelines

1. **Documentation**: Include clear docstrings and examples
2. **Testing**: Add unit tests for all tools
3. **Error Handling**: Implement comprehensive error handling
4. **Security**: Validate inputs and prevent path traversal
5. **Performance**: Use appropriate timeouts and resource limits

### Submission Process

1. Create tool in `equitrcoder/tools/custom/`
2. Add tests in `tests/custom_tools/`
3. Update relevant profile configurations
4. Add documentation and examples
5. Submit pull request with description

---

## Examples

See the existing custom tools for reference:
- `testing_tools.py` - Testing and QA tools
- `backend_tools.py` - API and database tools
- `frontend_tools.py` - Build and development tools
- `devops_tools.py` - Deployment and infrastructure tools

Each file contains multiple related tools with comprehensive implementations and error handling.