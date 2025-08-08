# Tool Logging and Multi-Model Support Guide

This guide covers the new features added to EQUITR-Coder:

1. **Tool Call Logging** - Track and analyze all tool executions
2. **Multi-Agent Separate Models** - Use different models for supervisor and workers

## Tool Call Logging

### Overview

Tool call logging allows you to track every tool execution in your EQUITR-Coder sessions, including:
- Which tools were called and when
- Tool arguments and results
- Execution duration and success/failure status
- Comprehensive statistics and analytics

### Enabling Tool Logging

#### Programmatic API

```python
from equitrcoder.api import EquitrAPI, SyncEquitrAPI

# Async API
async with EquitrAPI(
    repo_path="./my_project",
    log_tool_calls=True,                    # Enable logging
    tool_log_file="my_tool_calls.log",      # Log file path
) as api:
    response = await api.chat("Create a Python script")
    
    # Get statistics
    stats = api.get_tool_call_stats()
    print(f"Total tool calls: {stats['total_calls']}")
    
    # Export logs
    api.export_tool_logs("detailed_logs.json", format="json")

# Sync API
with SyncEquitrAPI(log_tool_calls=True) as api:
    response = api.chat("List files in current directory")
    logs = api.get_tool_call_logs(limit=10)
```

#### CLI Interface

```bash
# Interactive CLI
equitrcoder --log-tool-calls --tool-log-file "session_tools.log"

# Simple CLI
equitrcoder-simple --log-tool-calls --tool-log-file "tools.log"
```

### Tool Call Statistics

The logging system provides comprehensive analytics:

```python
stats = api.get_tool_call_stats()
print(stats)
# Output:
{
    "total_calls": 15,
    "successful_calls": 14,
    "failed_calls": 1,
    "success_rate": 0.933,
    "total_duration_ms": 2543.2,
    "average_duration_ms": 169.5,
    "tool_usage": {
        "read_file": {
            "count": 5,
            "success_count": 5,
            "total_duration_ms": 234.1
        },
        "write_file": {
            "count": 3,
            "success_count": 2,
            "total_duration_ms": 456.7
        }
    }
}
```

### Log File Format

Tool calls are logged in both structured (JSON) and human-readable formats:

```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "session_id": "session_abc123",
  "tool_name": "read_file",
  "tool_args": {
    "file_path": "src/main.py",
    "start_line": 1,
    "end_line": 50
  },
  "result": {
    "success": true,
    "content": "File contents...",
    "metadata": {}
  },
  "success": true,
  "duration_ms": 23.4,
  "error": null
}
```

## Multi-Agent Separate Models

### Overview

In multi-agent mode, you can now use different models for different roles:
- **Supervisor Model**: Handles task decomposition and coordination (typically a more powerful model)
- **Worker Model**: Executes individual tasks (can be a faster, more cost-effective model)

This allows you to optimize for both quality and cost.

### Configuration

#### Programmatic API

```python
# Use Claude 3.5 Sonnet for supervision, Haiku for workers
async with EquitrAPI(
    multi_agent=True,
    supervisor_model="anthropic/claude-3.5-sonnet",  # Powerful model
    worker_model="anthropic/claude-3-haiku",         # Fast model
) as api:
    response = await api.chat("Build a complete web application")
```

#### CLI Interface

```bash
# Interactive CLI
equitrcoder --multi-agent \
    --supervisor-model "anthropic/claude-3.5-sonnet" \
    --worker-model "anthropic/claude-3-haiku"

# Simple CLI
equitrcoder-simple --multi-agent \
    --supervisor-model "openai/gpt-4" \
    --worker-model "openai/gpt-3.5-turbo"
```

#### Configuration Files

Add to your YAML configuration:

```yaml
orchestrator:
  use_multi_agent: true
  supervisor_model: "anthropic/claude-3.5-sonnet"
  worker_model: "anthropic/claude-3-haiku"
  log_tool_calls: true
  tool_log_file: "tool_calls.log"
```

### Model Selection Strategy

**Supervisor Model (Task Decomposition & Coordination):**
- Use more powerful models (Claude 3.5 Sonnet, GPT-4)
- Better at complex reasoning and planning
- Handles fewer calls, so cost impact is lower

**Worker Model (Task Execution):**
- Use faster, more cost-effective models (Claude 3 Haiku, GPT-3.5 Turbo)
- Handles many parallel tasks
- Optimized for specific tool execution

### Example Configurations

```python
# Quality-focused (both powerful models)
config_quality = {
    "supervisor_model": "anthropic/claude-3.5-sonnet",
    "worker_model": "anthropic/claude-3.5-sonnet"
}

# Cost-optimized (fast models)
config_cost = {
    "supervisor_model": "anthropic/claude-3-haiku",
    "worker_model": "anthropic/claude-3-haiku"
}

# Balanced (powerful supervisor, fast workers)
config_balanced = {
    "supervisor_model": "anthropic/claude-3.5-sonnet",
    "worker_model": "anthropic/claude-3-haiku"
}
```

## Complete Example

```python
#!/usr/bin/env python3
"""
Complete example using both tool logging and multi-model support.
"""

import asyncio
from equitrcoder.api import EquitrAPI

async def main():
    async with EquitrAPI(
        repo_path="./my_project",
        multi_agent=True,
        supervisor_model="anthropic/claude-3.5-sonnet",
        worker_model="anthropic/claude-3-haiku", 
        log_tool_calls=True,
        tool_log_file="project_tools.log",
        budget=10.0,  # $10 budget
    ) as api:
        
        # Complex project creation
        response = await api.chat("""
        Create a complete Python web API with:
        1. FastAPI framework
        2. Database models with SQLAlchemy
        3. Authentication system
        4. CRUD operations
        5. API documentation
        6. Docker configuration
        7. Unit tests
        """)
        
        print("🚀 Project created!")
        
        # Analyze tool usage
        stats = api.get_tool_call_stats()
        print(f"\n📊 Tool Statistics:")
        print(f"  Total calls: {stats['total_calls']}")
        print(f"  Success rate: {stats['success_rate']:.1%}")
        print(f"  Total time: {stats['total_duration_ms']/1000:.1f}s")
        
        # Show most used tools
        tool_usage = stats['tool_usage']
        sorted_tools = sorted(tool_usage.items(), 
                            key=lambda x: x[1]['count'], 
                            reverse=True)
        
        print(f"\n🔧 Top Tools:")
        for tool_name, usage in sorted_tools[:5]:
            print(f"  {tool_name}: {usage['count']} calls")
        
        # Export detailed logs
        api.export_tool_logs("detailed_analysis.json")
        print(f"\n💾 Exported logs to detailed_analysis.json")

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration Reference

### CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--log-tool-calls` | Enable tool call logging | `False` |
| `--tool-log-file` | Path to tool log file | `"tool_calls.log"` |
| `--supervisor-model` | Model for supervisor agent | Uses main model |
| `--worker-model` | Model for worker agents | Uses main model |

### API Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `log_tool_calls` | `bool` | Enable tool logging |
| `tool_log_file` | `str` | Log file path |
| `supervisor_model` | `str` | Supervisor model name |
| `worker_model` | `str` | Worker model name |

### Configuration File

```yaml
orchestrator:
  use_multi_agent: true
  supervisor_model: "anthropic/claude-3.5-sonnet"
  worker_model: "anthropic/claude-3-haiku"
  log_tool_calls: true
  tool_log_file: "tool_calls.log"
```

## Best Practices

### Tool Logging
1. **Enable for debugging**: Use tool logging to understand execution patterns
2. **Monitor performance**: Track tool duration to identify bottlenecks
3. **Analyze failures**: Review failed tool calls to improve reliability
4. **Export for analysis**: Use JSON export for detailed analysis with external tools

### Multi-Model Configuration
1. **Supervisor quality**: Use powerful models for task decomposition
2. **Worker efficiency**: Use fast models for routine task execution
3. **Cost optimization**: Balance model capabilities with budget constraints
4. **Testing**: Test different model combinations for your use cases

## Troubleshooting

### Common Issues

**Tool logging not working:**
- Ensure `log_tool_calls=True` is set
- Check file permissions for log file path
- Verify the logging directory exists

**Multi-model setup fails:**
- Verify both models are available in your configuration
- Check API keys for different providers
- Ensure models support function calling

**High costs with multi-agent:**
- Use cost-effective worker models (Haiku, GPT-3.5 Turbo)
- Set appropriate budget limits
- Monitor tool call statistics

For more examples, see `examples/tool_logging_example.py`. 