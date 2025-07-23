# EQUITR Coder Configuration Guide

Complete guide to configuring EQUITR Coder for different environments and use cases.

## Configuration File Location

EQUITR Coder uses a YAML configuration file located at:
```
~/.equitr/config.yaml
```

## Default Configuration

```yaml
# EQUITR Coder Configuration
llm:
  model: "gpt-4o-mini"  # Default model - change as needed
  temperature: 0.3
  max_tokens: 4000
  budget: 25.0  # USD limit
  # api_key: "your-api-key-here"  # Set via environment variable instead

orchestrator:
  use_multi_agent: false
  max_iterations: 20

session:
  session_dir: "~/.equitr/sessions"
  max_context: 32000

repository:
  ignore_patterns:
    - "*.log"
    - "*.tmp"
    - "node_modules/"
    - "__pycache__/"
    - ".git/"
    - ".env"

git:
  auto_commit: true
  commit_message_prefix: "🤖 EQUITR:"
```

## Configuration Sections

### 1. LLM Configuration

```yaml
llm:
  model: "gpt-4o-mini"        # Model to use
  temperature: 0.3            # Response randomness (0.0-1.0)
  max_tokens: 4000           # Maximum response length
  budget: 25.0               # USD spending limit
  api_key: "sk-..."          # API key (use env var instead)
  api_base: "https://api.openai.com/v1"  # API endpoint
```

**Available Models:**
- `gpt-4o` - Most capable, highest cost
- `gpt-4o-mini` - Good balance of capability and cost
- `gpt-3.5-turbo` - Fast and economical
- `claude-3-haiku` - Anthropic's fast model
- `claude-3-sonnet` - Anthropic's balanced model

### 2. Orchestrator Configuration

```yaml
orchestrator:
  use_multi_agent: false      # Enable multi-agent mode
  max_iterations: 20          # Maximum interaction loops
  worker_timeout: 600         # Worker timeout in seconds
  max_workers: 3              # Maximum parallel workers
```

### 3. Session Configuration

```yaml
session:
  session_dir: "~/.equitr/sessions"  # Session storage directory
  max_context: 32000                 # Context window size
  auto_save: true                    # Auto-save sessions
  max_sessions: 100                  # Maximum stored sessions
```

### 4. Repository Configuration

```yaml
repository:
  ignore_patterns:           # Files/directories to ignore
    - "*.log"
    - "*.tmp"
    - "node_modules/"
    - "__pycache__/"
    - ".git/"
    - ".env"
    - "venv/"
    - "env/"
  max_file_size: 1048576     # Max file size (1MB)
  max_files: 1000            # Max files to index
```

### 5. Git Configuration

```yaml
git:
  auto_commit: true                      # Auto-commit changes
  commit_message_prefix: "🤖 EQUITR:"    # Commit message prefix
  auto_push: false                       # Auto-push to remote
  branch_prefix: "equitr/"               # Branch prefix for new branches
```

## Environment Variables

EQUITR Coder supports these environment variables:

```bash
# API Keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-..."

# Configuration
export EQUITR_CONFIG_PATH="/custom/path/config.yaml"
export EQUITR_SESSION_DIR="/custom/sessions"
export EQUITR_PROFILE="production"

# Model Configuration
export EQUITR_MODEL="gpt-4o"
export EQUITR_BUDGET="50.0"
export EQUITR_MULTI_AGENT="true"
```

Environment variables override configuration file settings.

## Configuration Profiles

You can create multiple configuration profiles:

```bash
# Create profile-specific configs
~/.equitr/config.yaml         # Default profile
~/.equitr/config-dev.yaml     # Development profile
~/.equitr/config-prod.yaml    # Production profile
```

Use profiles with:
```bash
equitrcoder --profile dev
equitrcoder --profile prod
```

### Example Development Profile

```yaml
# ~/.equitr/config-dev.yaml
llm:
  model: "gpt-4o-mini"
  temperature: 0.5
  budget: 10.0

orchestrator:
  use_multi_agent: false
  max_iterations: 15

git:
  auto_commit: false
```

### Example Production Profile

```yaml
# ~/.equitr/config-prod.yaml
llm:
  model: "gpt-4o"
  temperature: 0.1
  budget: 100.0

orchestrator:
  use_multi_agent: true
  max_iterations: 30

git:
  auto_commit: true
  auto_push: true
```

## Model-Specific Configurations

### OpenAI Configuration

```yaml
llm:
  model: "gpt-4o"
  api_key: "${OPENAI_API_KEY}"
  api_base: "https://api.openai.com/v1"
  temperature: 0.3
  max_tokens: 4000
```

### Anthropic Configuration

```yaml
llm:
  model: "claude-3-sonnet"
  api_key: "${ANTHROPIC_API_KEY}"
  api_base: "https://api.anthropic.com"
  temperature: 0.3
  max_tokens: 4000
```

### Custom/Local Model Configuration

```yaml
llm:
  model: "custom-model"
  api_key: "not-needed"
  api_base: "http://localhost:8000/v1"
  temperature: 0.3
  max_tokens: 4000
```

## Multi-Agent Configuration

For complex projects, configure multi-agent mode:

```yaml
orchestrator:
  use_multi_agent: true
  max_workers: 5              # Number of parallel workers
  worker_timeout: 900         # 15 minutes timeout
  coordination_interval: 30   # Coordination check interval
  
  # Worker specialization
  workers:
    file_worker:
      max_files: 50
      allowed_extensions: [".py", ".js", ".ts"]
    
    code_worker:
      max_functions: 20
      code_style: "pep8"
    
    analysis_worker:
      max_analysis_depth: 3
      include_dependencies: true
```

## Budget and Cost Management

```yaml
llm:
  budget: 50.0                # Total budget in USD
  budget_warning: 40.0        # Warning threshold
  cost_tracking: true         # Enable cost tracking
  
  # Model-specific pricing (optional)
  pricing:
    gpt-4o:
      input: 0.005   # Per 1K tokens
      output: 0.015  # Per 1K tokens
    gpt-4o-mini:
      input: 0.0015
      output: 0.006
```

## Documentation Configuration

```yaml
documentation:
  auto_generate: true         # Always generate docs
  min_length: 100            # Minimum document length
  save_to_files: true        # Save docs to files
  
  templates:
    requirements: "custom_requirements_template.md"
    design: "custom_design_template.md"
    todos: "custom_todos_template.md"
```

## Security Configuration

```yaml
security:
  allowed_commands: ["git", "npm", "pip", "python"]
  blocked_patterns: ["rm -rf", "sudo", "chmod 777"]
  max_command_length: 1000
  sandbox_mode: false
```

## Troubleshooting Common Issues

### Issue: Configuration not loaded

```bash
# Check config file exists
ls -la ~/.equitr/config.yaml

# Check config syntax
python -c "import yaml; yaml.safe_load(open('~/.equitr/config.yaml'))"

# Recreate default config
rm ~/.equitr/config.yaml
equitrcoder  # Will create default config
```

### Issue: API key not found

```bash
# Check environment variable
echo $OPENAI_API_KEY

# Set temporarily
export OPENAI_API_KEY="your-key"

# Add to shell profile
echo 'export OPENAI_API_KEY="your-key"' >> ~/.bashrc
source ~/.bashrc
```

### Issue: Budget exceeded

```yaml
# Increase budget in config
llm:
  budget: 100.0

# Or use CLI override
equitrcoder --budget 100.0
```

### Issue: Multi-agent mode not working

```yaml
# Check model compatibility
llm:
  model: "gpt-4o"  # Ensure model supports function calling

# Enable multi-agent explicitly
orchestrator:
  use_multi_agent: true
```

### Issue: Sessions not saving

```bash
# Check session directory
ls -la ~/.equitr/sessions/

# Check permissions
chmod 755 ~/.equitr/sessions/

# Check disk space
df -h ~/.equitr/
```

## Advanced Configuration Examples

### High-Performance Setup

```yaml
llm:
  model: "gpt-4o"
  temperature: 0.1
  max_tokens: 8000
  budget: 200.0

orchestrator:
  use_multi_agent: true
  max_workers: 8
  worker_timeout: 1200

session:
  max_context: 64000
  auto_save: true
```

### Development Setup

```yaml
llm:
  model: "gpt-4o-mini"
  temperature: 0.5
  budget: 10.0

orchestrator:
  use_multi_agent: false
  max_iterations: 10

git:
  auto_commit: false
  auto_push: false
```

### Enterprise Setup

```yaml
llm:
  model: "gpt-4o"
  api_base: "https://your-enterprise-api.com/v1"
  budget: 1000.0

orchestrator:
  use_multi_agent: true
  max_workers: 10

security:
  sandbox_mode: true
  allowed_commands: ["git", "docker", "kubectl"]

documentation:
  auto_generate: true
  templates:
    requirements: "/company/templates/requirements.md"
```

## Configuration Validation

EQUITR Coder validates configuration on startup:

```bash
# Test configuration
equitrcoder --version  # Will show config errors if any

# Validate specific profile
equitrcoder --profile prod --version
```

## Performance Tuning

### For Speed

```yaml
llm:
  model: "gpt-4o-mini"
  temperature: 0.1
  max_tokens: 2000

orchestrator:
  max_iterations: 10
  use_multi_agent: true
```

### For Quality

```yaml
llm:
  model: "gpt-4o"
  temperature: 0.3
  max_tokens: 8000

orchestrator:
  max_iterations: 30
  use_multi_agent: true
```

### For Cost Efficiency

```yaml
llm:
  model: "gpt-4o-mini"
  temperature: 0.3
  budget: 5.0

orchestrator:
  max_iterations: 15
  use_multi_agent: false
```

## Configuration Best Practices

1. **Use Environment Variables for Secrets**
   ```bash
   export OPENAI_API_KEY="sk-..."
   # Don't put API keys in config files
   ```

2. **Set Appropriate Budgets**
   ```yaml
   llm:
     budget: 25.0  # Start conservative
     budget_warning: 20.0
   ```

3. **Choose Right Model for Task**
   - Simple tasks: `gpt-4o-mini`
   - Complex tasks: `gpt-4o`
   - Multi-agent: `gpt-4o` (better coordination)

4. **Use Profiles for Different Environments**
   ```bash
   equitrcoder --profile dev    # Development
   equitrcoder --profile prod   # Production
   ```

5. **Configure Git Appropriately**
   ```yaml
   git:
     auto_commit: true    # For documentation
     auto_push: false     # Manual review recommended
   ```

This configuration guide helps you customize EQUITR Coder for your specific needs and environments.