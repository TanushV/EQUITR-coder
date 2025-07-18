# EQUITR Coder Usage Guide

Complete guide to installing and using EQUITR Coder - the interactive AI coding assistant with mandatory documentation generation.

## Installation

### Quick Install
```bash
# Clone the repository
git clone https://github.com/equitr/EQUITR-coder.git
cd EQUITR-coder

# Run the installation script
./install.sh
```

### Manual Install
```bash
# Create virtual environment (recommended)
python3 -m venv equitr-env
source equitr-env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install EQUITR Coder
pip install -e .

# Create config directory
mkdir -p ~/.equitr
```

### Set API Key
```bash
# Set your OpenAI API key
export OPENAI_API_KEY="your-api-key-here"

# Or add to your shell profile
echo 'export OPENAI_API_KEY="your-api-key-here"' >> ~/.bashrc
```

## Basic Usage

### Start EQUITR Coder
```bash
equitrcoder
```

This is the ONLY command you need. EQUITR Coder is designed to be interactive-only.

### Command Options
```bash
equitrcoder --help                    # Show help
equitrcoder --version                 # Show version
equitrcoder --model gpt-4o            # Use specific model
equitrcoder --multi-agent             # Enable multi-agent mode
equitrcoder --budget 50.0             # Set budget limit
equitrcoder --repo /path/to/project   # Work in specific directory
```

## Interactive Workflow

EQUITR Coder enforces a structured workflow:

1. **Planning Conversation** - AI asks questions to understand requirements
2. **Documentation Generation** - Creates requirements, design, and todo documents
3. **Review & Approval** - User reviews and approves documentation
4. **Implementation** - AI implements using documentation as context

## Configuration

### Configuration File
Location: `~/.equitr/config.yaml`

```yaml
# EQUITR Coder Configuration
llm:
  model: "gpt-4o-mini"  # Model to use
  temperature: 0.3      # Response randomness (0-1)
  max_tokens: 4000      # Maximum response length
  budget: 25.0          # USD spending limit

orchestrator:
  use_multi_agent: false  # Enable multi-agent mode
  max_iterations: 20      # Maximum interaction loops

session:
  session_dir: "~/.equitr/sessions"  # Session storage
  max_context: 32000                 # Context window size

repository:
  ignore_patterns:       # Files to ignore
    - "*.log"
    - "node_modules/"
    - "__pycache__/"
    - ".git/"

git:
  auto_commit: true      # Auto-commit changes
  commit_message_prefix: "🤖 EQUITR:"
```

### Environment Variables
```bash
# Required
export OPENAI_API_KEY="your-api-key"

# Optional
export EQUITR_CONFIG_PROFILE="production"
export EQUITR_SESSION_DIR="/custom/session/path"
```

## Interactive Commands

Within the EQUITR Coder session:

```bash
/quit           # Exit session
/clear          # Clear conversation history
/status         # Show session status
/multi-agent    # Toggle multi-agent mode
/help           # Show help
```

## Documentation Structure

Every project generates three mandatory documents:

```
project/
├── docs/
│   ├── requirements.md  # Functional & non-functional requirements
│   ├── design.md        # System architecture & design
│   └── todos.md         # Prioritized implementation tasks
├── [your project files]
└── README.md
```

## Multi-Agent Mode

Enable multi-agent mode for complex projects:

```bash
equitrcoder --multi-agent
```

### When to Use Multi-Agent Mode
- Complex system architectures
- Multiple interconnected components
- Microservices projects
- Large-scale applications

### How Multi-Agent Mode Works
1. **Supervisor Agent** - Coordinates and manages tasks
2. **Worker Agents** - Execute specific tasks in parallel
3. **Message Pool** - Enables inter-agent communication
4. **Task Queue** - Manages work distribution

## Project Types

### Simple API Project
```bash
equitrcoder --repo ./my-api
```
Perfect for: REST APIs, single-service applications

### Frontend Application
```bash
equitrcoder --repo ./my-frontend
```
Perfect for: React/Vue/Angular applications, dashboards

### Full-Stack Application
```bash
equitrcoder --multi-agent --repo ./my-fullstack
```
Perfect for: Complete web applications, complex systems

### Microservices Architecture
```bash
equitrcoder --multi-agent --budget 100.0 --repo ./my-microservices
```
Perfect for: Distributed systems, enterprise applications

## Best Practices

### 1. Prepare Your Requirements
- Think about core functionality
- Consider technology preferences
- Identify constraints and dependencies

### 2. Be Specific in Conversations
- Mention specific technologies when preferred
- Describe user workflows clearly
- Clarify performance requirements

### 3. Review Documentation Carefully
- Verify requirements match your vision
- Check design decisions
- Ensure todos are comprehensive

### 4. Use Appropriate Mode
- **Single-agent**: Simple projects, APIs, frontend apps
- **Multi-agent**: Complex systems, microservices, large projects

## Troubleshooting

### Common Issues

**Issue: "No API key found"**
```bash
export OPENAI_API_KEY="your-api-key-here"
```

**Issue: "Command not found: equitrcoder"**
```bash
pip install -e .
# Or check if you're in the right virtual environment
```

**Issue: "Budget exceeded"**
```bash
equitrcoder --budget 50.0
# Or edit ~/.equitr/config.yaml
```

**Issue: "Documentation generation failed"**
- Check internet connection
- Verify API key is valid
- Try with a different model

**Issue: "Multi-agent mode not working"**
- Ensure model supports function calling
- Check budget limits
- Verify configuration

### Debug Mode
```bash
equitrcoder --model gpt-4o --budget 10.0
# Use status command to check session info
/status
```

### Reset Configuration
```bash
rm -rf ~/.equitr/
mkdir -p ~/.equitr/sessions
# Reinstall will recreate default config
```

## Advanced Usage

### Custom Model Configuration
```yaml
llm:
  model: "gpt-4o"
  api_base: "https://api.openai.com/v1"
  temperature: 0.2
  max_tokens: 4000
```

### Multiple Profiles
```bash
equitrcoder --profile development
equitrcoder --profile production
```

### Session Management
```bash
# Resume previous session
equitrcoder --session my-session-id

# Sessions are stored in ~/.equitr/sessions/
```

### Custom Repository Settings
```yaml
repository:
  ignore_patterns:
    - "*.log"
    - "dist/"
    - "build/"
    - "node_modules/"
  max_file_size: 1048576  # 1MB
```

## Tips & Tricks

### 1. Optimize for Your Use Case
- Use `gpt-4o-mini` for development/testing
- Use `gpt-4o` for production projects
- Adjust budget based on project complexity

### 2. Leverage Documentation
- Generated docs become context for all future requests
- Edit docs manually if needed
- Use docs to onboard team members

### 3. Multi-Agent Efficiency
- Enable for projects with 3+ independent components
- Higher budgets recommended for complex coordination
- Monitor agent communication for insights

### 4. Session Management
- Use descriptive session names
- Clear sessions when switching projects
- Resume sessions for iterative development

## Support

### Getting Help
- Use `/help` in interactive mode
- Check `/status` for session information
- Review generated documentation in `docs/`

### Community
- GitHub Issues: Report bugs and request features
- Discussions: Share workflows and best practices
- Documentation: Comprehensive guides and examples

### Configuration Help
```bash
equitrcoder --help
cat ~/.equitr/config.yaml
ls -la ~/.equitr/sessions/
```

## Examples

See the `examples/` directory for:
- Quick start guide
- Multi-agent workflows
- Configuration examples
- Common use cases

## Next Steps

1. **Start Simple**: Try a basic API project
2. **Explore Multi-Agent**: Test with a complex system
3. **Customize Configuration**: Adjust for your workflow
4. **Share & Collaborate**: Use generated documentation for team projects

EQUITR Coder transforms your development workflow with AI-powered planning, documentation, and implementation. The mandatory documentation ensures consistent, well-architected projects every time.