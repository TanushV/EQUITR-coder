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

profiles:
  default: default
  available:
    - ml_researcher
    - app_developer

  settings:
    profiles_directory: "equitrcoder/profiles"
    allow_empty_additional_tools: true
    profile_search_paths:
      - "{project}/.equitr/profiles"
      - "{home}/extensions/profiles"

extensions:
  tools:
    - "{project}/.equitr/tools"
    - "{home}/extensions/tools"
  profiles:
    - "{project}/.equitr/profiles"
    - "{home}/extensions/profiles"
  modes:
    - "{project}/.equitr/modes"
    - "{home}/extensions/modes"
  mcp:
    - "{project}/.equitr/mcp"
    - "{home}/extensions/mcp"

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

### 3. MCP Servers Configuration

MCP servers are configured via JSON, separate from the YAML config. The loader searches in this order:
- `EQUITR_MCP_SERVERS` (env var) → path to a JSON file
- `~/.EQUITR-coder/mcp_servers.json`
- Packaged default at `equitrcoder/config/mcp_servers.json`

Example:

```json
{
  "mcpServers": {
    "sqlite": {
      "command": "uvx",
      "args": ["mcp-server-sqlite", "--db-path", "./test.db"],
      "env": {},
      "transport": "stdio"
    }
  }
}
```

Each configured server becomes available as a tool named `mcp:<serverName>` with arguments `{ "tool": "<remoteToolName>", "arguments": { ... } }`.

  max_iterations: 20          # Maximum interaction loops
  worker_timeout: 600         # Worker timeout in seconds
  max_workers: 3              # Maximum parallel workers
  supervisor_model: "o3"     # Strong model for supervisor
  worker_model: "gpt-4.1"   # Weak model for workers
  log_tool_calls: true        # Enable tool logging
  tool_log_file: "tools.log" # Tool log path
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

### 5. Extension Search Paths

Extensions (custom tools, profiles, modes, and MCP connectors) are resolved by
combining multiple directories in priority order:

1. Environment overrides (`EQUITR_TOOLS_PATH`, `EQUITR_PROFILES_PATH`,
   `EQUITR_MODES_PATH`, `EQUITR_MCP_PATH`)
2. Global extension roots (`EQUITR_EXTENSIONS_DIR`)
3. Project-local `.equitr/<kind>/` directories
4. User workspace (`~/.EQUITR-coder/extensions/<kind>`)
5. Packaged defaults bundled with EQUITR Coder

Use the `extensions` section in `default.yaml` to add additional directories or
change the order. This keeps package installs clean by moving customisations to
user-accessible folders.

### 6. Git Configuration

```yaml
git:
  auto_commit: true                      # Auto-commit changes
  commit_message_prefix: "🤖 EQUITR:"    # Commit message prefix
  auto_push: false                       # Auto-push to remote
  branch_prefix: "equitr/"               # Branch prefix for new branches
  auto_init: true                        # Auto-init new repos
  gitignore_template: "python"          # Auto-generate .gitignore
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
export EQUITR_HOME="/opt/equitr"
export EQUITR_EXTENSIONS_DIR="/opt/equitr/extensions"
export EQUITR_TOOLS_PATH="/project/.equitr/tools"
export EQUITR_PROFILES_PATH="/project/.equitr/profiles"
export EQUITR_MODES_PATH="/project/.equitr/modes"
export EQUITR_MCP_PATH="/project/.equitr/mcp"

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