# EQUITR Coder

Modular AI coding assistant supporting single and multi-agent workflows and an ML-focused researcher mode. Includes an advanced TUI, automatic audit system, and intelligent model optimization.

## Quick Start

- Install (latest from PyPI):
  ```bash
pip install equitrcoder
  ```
- Optional extras:
  - API server: `pip install "equitrcoder[api]"`
  - TUI: `pip install "equitrcoder[tui]"`

## Configure API keys (env vars)

Set whatever providers you plan to use:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `OPENROUTER_API_KEY`
- `MOONSHOT_API_KEY`
- `GROQ_API_KEY`



Export examples (macOS/Linux):
```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=...
export OPENROUTER_API_KEY=...
```

## TUI (Interactive)

- Launch TUI:
  ```bash
equitrcoder tui
  ```
- Startup screen: pick Supervisor, Worker, Mode, and enter your first task
- Chat commands (slash-only):
  - `/set supervisor <model>`
  - `/set worker <model>`
  - `/set mode <single|multi-parallel|multi-seq|research>`
- Keys:
  - Enter: submit
  - Ctrl+C: exit

Troubleshooting:
- If you see a Textual widget error, ensure `textual` and `rich` are installed.
- If you have no API keys, you can still launch the TUI, but model listings will be minimal and execution may fail when contacting providers.

## CLI

- Single:
  ```bash
equitrcoder single "Build a small API" --model moonshot/kimi-k2-0711-preview
  ```
- Multi (parallel phases):
  ```bash
equitrcoder multi "Ship a feature" --supervisor-model moonshot/kimi-k2-0711-preview \
  --worker-model moonshot/kimi-k2-0711-preview --workers 3 --max-cost 15 \
  --team backend_dev,frontend_dev,qa_engineer
  ```
- Multi (sequential execution):
  ```bash
equitrcoder multi "Ship a feature" --supervisor-model moonshot/kimi-k2-0711-preview \
  --worker-model moonshot/kimi-k2-0711-preview --workers 3 --max-cost 15 \
  --team backend_dev,frontend_dev,qa_engineer --execution-mode sequential
  ```
- Research (ML only):
  ```bash
equitrcoder research "Evaluate model X on dataset Y" \
  --supervisor-model moonshot/kimi-k2-0711-preview --worker-model moonshot/kimi-k2-0711-preview \
  --workers 3 --max-cost 12 --team ml_researcher,data_engineer,experiment_runner
  ```
- Tools management:
  ```bash
equitrcoder tools --list              # List all available tools
equitrcoder tools --discover          # Discover and register tools
  ```
- Models listing:
  ```bash
equitrcoder models                    # List all available AI models
equitrcoder models --provider openai  # Filter by provider
  ```

## Programmatic Usage

```python
from equitrcoder import EquitrCoder, TaskConfiguration

coder = EquitrCoder(mode="single", repo_path=".")
config = TaskConfiguration(description="Refactor module X", max_cost=2.0, max_iterations=20)
result = await coder.execute_task("Refactor module X", config)
print(result.success, result.cost, result.iterations)
```

- Multi-agent and researcher programmatic configs are available via `MultiAgentTaskConfiguration` and `ResearchTaskConfiguration`.

## API Server

- Start server (requires extras):
  ```bash
equitrcoder api --host 0.0.0.0 --port 8000
  ```
- Endpoints:
  - `GET /` root
  - `GET /health`
  - `GET /tools`
  - `POST /single/execute`
  - `POST /multi/create`
  - `POST /multi/{id}/execute`
  - `GET /multi/{id}/status`
  - `DELETE /multi/{id}`

## Audit System

EQUITR Coder includes a comprehensive audit pipeline that automatically runs after task completion:

- **Automatic Testing**: Generates and runs audit tests for each completed task group
- **Quality Assurance**: Validates code changes against requirements and design specifications
- **Failure Handling**: Automatically marks failed audits for remediation and adds follow-up tasks
- **Comprehensive Reports**: Generates detailed audit reports with test results and commentary

To run the audit monitor manually:
```bash
python -m equitrcoder.cli.audit_monitor \
  --todo-file docs/<task_name>/todos.json \
  --task-name <task_name> \
  --sections-file docs/<task_name>/group_sections.json \
  --poll-interval 10
```

Set the audit token for write operations:
```bash
export EQUITR_AUDIT_TOKEN=your-secret
```

See `docs/AUDIT_SYSTEM.md` for complete documentation.

## Configuration

- Default config lives in `equitrcoder/config/default.yaml`.
- User overrides: `~/.EQUITR-coder/config.yaml`.
- Env overrides supported for selected keys (see code and docs).
- `session.max_context: "auto"` is supported and normalized automatically.

### Advanced Features

- **Intelligent Model Optimization**: Automatic reasoning/thinking budget allocation for supported models (o3, o1, etc.)
- **Accurate Cost Tracking**: Model-aware cost calculation using litellm for precise billing
- **Automatic Requirements Installation**: Auto-installs Python requirements for venv-based experiments
- **Specialized Agent Profiles**: Choose from 10+ specialized profiles (backend_dev, frontend_dev, qa_engineer, ml_researcher, etc.)

### MCP Servers (Optional)

- Enable MCP by installing the Python SDK:

```bash
pip install modelcontextprotocol
```

- Declare servers in `~/.EQUITR-coder/mcp_servers.json` or set `EQUITR_MCP_SERVERS`.
Each server appears as a tool `mcp:<serverName>` that forwards to the remote tools.
See `docs/MCP_INTEGRATION_GUIDE.md`.

## Examples

See `examples/` for patterns:
- `create_react_website.py`
- `mario_parallel_example.py`
- `research_programmatic_example.py`

## Troubleshooting

- Missing models or keys: ensure relevant env vars are set. The TUI will still load, but execution may fail when contacting providers.
- Textual errors: install TUI deps: `pip install textual rich`.
- Git integration issues: run inside a git repo or disable with `git_enabled=False` in programmatic usage. 