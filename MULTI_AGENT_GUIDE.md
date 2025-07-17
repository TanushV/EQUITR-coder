# Multi-Agent Orchestration Guide

EQUITR Coder now supports a **strong/weak agent paradigm** that leverages the power of multiple AI models working together. This guide explains how to use this advanced feature.

## Overview

The multi-agent system consists of:
- **Supervisor Agent** (Strong Model): GPT-4 or equivalent for complex reasoning and strategic guidance
- **Worker Agents** (Weak Model): GPT-3.5 or equivalent for routine tasks and implementation

## Quick Start

### Command Line Usage

```bash
# Enable multi-agent mode
EQUITR-coder chat --multi-agent "Create a REST API with proper error handling"

# Or use short flag
EQUITR-coder chat -M "Design a scalable microservice architecture"

# Interactive mode with multi-agent
EQUITR-coder interactive --multi-agent
```

### Configuration

Add to your `~/.equitr/config.yaml`:

```yaml
orchestrator:
  use_multi_agent: true
  
llm:
  model: "gpt-4o"  # Supervisor model
  # Worker model uses the same by default, but you can configure separately
```

## How It Works

### 1. Automatic Escalation
Complex tasks automatically escalate to the supervisor for strategic guidance.

### 2. Tool Consultation
Worker agents can consult the supervisor using the `ask_supervisor` tool when:
- Facing architectural decisions
- Encountering complex bugs
- Needing design pattern guidance
- Planning large refactors

### 3. Cost Optimization
- Routine tasks handled by cost-effective worker models
- Complex reasoning delegated to powerful supervisor models
- Transparent cost tracking for both models

## Use Cases

### ✅ Perfect for Multi-Agent Mode
- **System Architecture**: Design patterns, microservices, database schemas
- **Complex Refactoring**: Large-scale code reorganization
- **Performance Optimization**: Bottleneck analysis and optimization strategies
- **Security Reviews**: Vulnerability assessment and security patterns
- **API Design**: RESTful design, GraphQL schemas, OpenAPI specs

### 🚫 Stick to Single Agent Mode
- Simple file operations
- Basic bug fixes
- Documentation updates
- Small feature additions

## Examples

### Example 1: REST API Design
```bash
EQUITR-coder chat -M "Design a RESTful API for a user management system with authentication, rate limiting, and proper error handling"
```

**What happens:**
1. Worker agent analyzes requirements
2. Supervisor provides architectural guidance
3. Worker implements the actual code
4. Supervisor reviews critical security aspects

### Example 2: Database Schema Design
```bash
EQUITR-coder chat -M "Create a scalable database schema for an e-commerce platform with products, orders, users, and inventory tracking"
```

### Example 3: Performance Optimization
```bash
EQUITR-coder chat -M "Optimize this slow Python function that's processing large datasets"
```

## Advanced Usage

### Custom Model Configuration

```yaml
# ~/.equitr/config.yaml
llm:
  provider: "litellm"
  model: "gpt-4o"  # Supervisor
  api_base: "http://localhost:4000"
  
  models:
    supervisor:
      provider: "litellm"
      model: "gpt-4o"
      temperature: 0.1
    worker:
      provider: "litellm" 
      model: "gpt-3.5-turbo"
      temperature: 0.3

orchestrator:
  use_multi_agent: true
  max_iterations: 15
```

### Programmatic Usage

```python
from EQUITR_coder.core.config import config_manager
from EQUITR_coder.core.orchestrator import AgentOrchestrator

async def run_multi_agent():
    config = config_manager.load_config("default")
    config.orchestrator.use_multi_agent = True
    
    orchestrator = AgentOrchestrator(config, ".")
    
    result = await orchestrator.run(
        "Design a caching layer for a high-traffic web application"
    )
    
    print(f"Cost: ${result['cost']:.4f}")
    print(f"Content: {result['content']}")
```

## Cost Management

### Cost Breakdown
- **Worker Model**: ~$0.001-0.003 per 1K tokens (GPT-3.5)
- **Supervisor Model**: ~$0.01-0.03 per 1K tokens (GPT-4)
- **Total**: Typically 2-5x more cost-effective than using GPT-4 alone

### Budget Configuration
```yaml
llm:
  budget: 10.0  # $10 USD limit
```

## Troubleshooting

### Common Issues

**Q: The ask_supervisor tool isn't available**
A: Ensure multi-agent mode is enabled:
```bash
EQUITR-coder config-cmd  # Check current config
EQUITR-coder chat --multi-agent  # Enable for this session
```

**Q: Getting "no model specified" errors**
A: Configure your models:
```bash
EQUITR-coder models --discover  # Find available models
EQUITR-coder chat --model "gpt-4o" --multi-agent
```

**Q: High costs with multi-agent mode**
A: Consider:
- Using GPT-3.5 for both supervisor and worker (development)
- Setting budget limits
- Using single-agent mode for simple tasks

### Debug Mode

Enable verbose logging:
```bash
EQUITR-coder chat --multi-agent --verbose "Your task here"
```

## Best Practices

1. **Start Simple**: Begin with single-agent mode, enable multi-agent for complex tasks
2. **Monitor Costs**: Use budget limits and cost tracking
3. **Iterative Development**: Use supervisor for design, worker for implementation
4. **Context Matters**: Provide clear, specific requirements for better supervisor guidance
5. **Model Selection**: Use GPT-4 for supervisor, GPT-3.5 for workers in production

## Migration Guide

### From Single to Multi-Agent

1. **Test with same model**: Start with GPT-4 for both supervisor and worker
2. **Gradual transition**: Use multi-agent for specific complex tasks
3. **Monitor performance**: Track cost vs. quality improvements
4. **Optimize models**: Switch worker to GPT-3.5 once comfortable

### Configuration Examples

**Development Setup** (same model):
```yaml
orchestrator:
  use_multi_agent: true
llm:
  model: "gpt-4o-mini"
```

**Production Setup** (optimized):
```yaml
orchestrator:
  use_multi_agent: true
llm:
  model: "gpt-4o"  # Supervisor
  # Worker uses same by default, configure separately if needed
```