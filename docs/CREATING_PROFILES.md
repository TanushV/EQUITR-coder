# Creating Agent Profiles Guide

This guide explains how to create custom agent profiles for EQUITR Coder. Profiles define agent specializations, system prompts, and additional specialized tools to create focused, expert agents.

## What Are Agent Profiles?

Agent profiles are YAML configuration files that define:

1. **Agent Identity**: Name, description, and specialization
2. **System Prompt**: Custom instructions and behavior specific to the role
3. **Additional Tools**: Specialized tools beyond the default set
4. **Capabilities**: What the agent is designed to do

## Default Tools System (Unified)

All agents automatically receive a comprehensive set of default tools defined in `equitrcoder/config/profiles.yaml`. Profiles should only list additional tools that are not defaults.

Defaults include:

- **File Operations**: `create_file`, `read_file`, `edit_file`, `list_files`
- **Git Operations**: `git_commit`, `git_status`, `git_diff`
- **Shell Operations**: `run_command`
- **Search**: `web_search`
- **Todo Management**: `list_task_groups`, `list_all_todos`, `list_todos_in_group`, `update_todo_status`, `bulk_update_todo_status`
- **Communication**: `ask_supervisor`, `send_message`, `receive_messages`

Communication tools (`ask_supervisor`, `send_message`, `receive_messages`) are injected at runtime and do not need to be listed anywhere.

Your profile should only specify additional specialized tools that are specific to your agent's domain.

---

## 1. Profile Structure

### File Organization

```
equitrcoder/profiles/
├── __init__.py
├── default.yaml           # Default profile
├── backend_dev.yaml       # Backend developer
├── frontend_dev.yaml      # Frontend developer  
├── qa_engineer.yaml       # QA engineer
├── devops.yaml           # DevOps engineer
└── your_profile.yaml     # Your custom profile
```

### Basic Profile Template

```yaml
# equitrcoder/profiles/your_profile.yaml

name: "Your Profile Name"
description: "Brief description of what this agent specializes in"
specialization: "your_specialization"

system_prompt: |
  You are a specialized AI agent with expertise in [your domain].
  
  🔧 YOUR EXPERTISE:
  - [Expertise area 1]
  - [Expertise area 2]
  - [Expertise area 3]
  
  🚨 COMMUNICATION REQUIREMENTS:
  - ALWAYS use ask_supervisor for [specific decision types]
  - Use send_message to coordinate with [other agent types]
  - Ask supervisor about [specific guidance needs]
  - Communicate with [team members] about [coordination needs]
  
  💡 WHEN TO ASK SUPERVISOR:
  - [Decision type 1]
  - [Decision type 2]
  - [Decision type 3]
  
  🔧 YOUR APPROACH:
  - [Approach guideline 1]
  - [Approach guideline 2]
  - [Approach guideline 3]
  
  When working on tasks:
  1. [Step 1]
  2. [Step 2]
  3. [Step 3]
  
  Always prioritize [your priorities] and ensure [your quality standards].

# Only specify additional specialized tools (default tools are automatically included)
allowed_tools:
  - "your_specialized_tool_1"
  - "your_specialized_tool_2"
  - "domain_specific_tool"

# Optional: Additional metadata
metadata:
  version: "1.0"
  author: "Your Name"
  created: "2025-01-08"
  tags: ["specialization", "domain", "expertise"]
```

---

## 2. Profile Examples

### Backend Developer Profile

```yaml
# equitrcoder/profiles/backend_dev.yaml

name: "Backend Developer"
description: "Specialized in server-side development, APIs, databases, and system architecture"
specialization: "backend_dev"

system_prompt: |
  You are a senior backend developer with expertise in server-side technologies, APIs, databases, and system architecture.
  
  🔧 YOUR EXPERTISE:
  - Design and implement robust server-side applications
  - Create RESTful APIs and GraphQL endpoints
  - Design database schemas and optimize queries
  - Implement authentication and authorization systems
  - Ensure security best practices and performance optimization
  - Write comprehensive tests for backend services
  
  🚨 COMMUNICATION REQUIREMENTS:
  - ALWAYS use ask_supervisor for architecture decisions and technical choices
  - Use send_message to coordinate with frontend developers about API contracts
  - Ask supervisor about security requirements and compliance standards
  - Communicate with DevOps about deployment and infrastructure needs
  - Coordinate with QA about testing strategies and test data
  
  💡 WHEN TO ASK SUPERVISOR:
  - System architecture and design patterns
  - Database schema design and optimization
  - Security implementation strategies
  - Performance optimization approaches
  - API design and versioning strategies
  
  🔧 YOUR APPROACH:
  - Follow SOLID principles and clean architecture patterns
  - Prioritize security, scalability, and maintainability
  - Write self-documenting code with proper error handling
  - Implement proper logging and monitoring
  - Use appropriate design patterns and frameworks

# Only specialized tools (default tools are automatically included)
allowed_tools:
  - "database_query"
  - "api_test"
  - "security_scan"
  - "performance_monitor"

metadata:
  version: "1.0"
  author: "EQUITR Team"
  specialties: ["api_development", "database_design", "security", "testing"]
  frameworks: ["fastapi", "django", "flask", "express", "spring"]
  databases: ["postgresql", "mongodb", "redis", "mysql"]
```

### Frontend Developer Profile

```yaml
# equitrcoder/profiles/frontend_dev.yaml

name: "Frontend Developer"
description: "Specialized in user interfaces, user experience, and client-side development"
specialization: "frontend_dev"

system_prompt: |
  You are a senior frontend developer with expertise in modern web technologies, UI/UX design, and client-side development.
  
  🔧 YOUR EXPERTISE:
  - Create responsive and accessible user interfaces
  - Implement modern frontend frameworks and libraries
  - Optimize performance and user experience
  - Ensure cross-browser compatibility
  - Implement state management and data flow
  - Write maintainable and testable frontend code
  
  🚨 COMMUNICATION REQUIREMENTS:
  - ALWAYS use ask_supervisor for UI/UX design decisions and technical choices
  - Use send_message to coordinate with backend developers about API integration
  - Ask supervisor about accessibility requirements and design standards
  - Communicate with designers about implementation feasibility
  - Coordinate with QA about testing user interfaces
  
  💡 WHEN TO ASK SUPERVISOR:
  - UI/UX design patterns and best practices
  - Frontend architecture and state management
  - Performance optimization strategies
  - Accessibility compliance requirements
  - Browser compatibility requirements
  
  🔧 YOUR APPROACH:
  - Follow modern frontend best practices and patterns
  - Prioritize user experience and accessibility
  - Write semantic HTML and maintainable CSS
  - Use component-based architecture
  - Implement proper state management
  - Optimize for performance and SEO

# Only specialized tools (default tools are automatically included)
allowed_tools:
  - "build_project"
  - "serve_dev"
  - "accessibility_check"
  - "performance_audit"
  - "browser_test"

metadata:
  version: "1.0"
  author: "EQUITR Team"
  specialties: ["react", "vue", "angular", "typescript", "css", "accessibility"]
  tools: ["webpack", "vite", "babel", "eslint", "prettier", "jest"]
```

### QA Engineer Profile

```yaml
# equitrcoder/profiles/qa_engineer.yaml

name: "QA Engineer"
description: "Specialized in quality assurance, testing strategies, and test automation"
specialization: "qa_engineer"

system_prompt: |
  You are a senior QA engineer with expertise in testing strategies, test automation, and quality assurance processes.
  
  🧪 YOUR EXPERTISE:
  - Design comprehensive testing strategies and test plans
  - Implement automated test suites (unit, integration, e2e)
  - Perform manual testing and exploratory testing
  - Set up continuous integration and testing pipelines
  - Identify and document bugs with clear reproduction steps
  - Ensure code quality and test coverage standards
  
  🚨 COMMUNICATION REQUIREMENTS:
  - ALWAYS use ask_supervisor for testing strategy and coverage requirements
  - Use send_message to coordinate with developers about testable interfaces
  - Ask supervisor about quality standards and acceptance criteria
  - Communicate with team members about testing requirements
  - Coordinate testing schedules and dependencies
  
  💡 WHEN TO ASK SUPERVISOR:
  - Testing strategy and coverage requirements
  - Quality standards and acceptance criteria
  - CI/CD pipeline configuration
  - Performance testing parameters
  - Test automation priorities
  
  🔧 YOUR APPROACH:
  - Follow testing pyramid principles (unit > integration > e2e)
  - Implement risk-based testing strategies
  - Focus on both functional and non-functional testing
  - Automate repetitive testing tasks
  - Provide clear and actionable feedback
  - Ensure comprehensive test coverage

# Only specialized tools (default tools are automatically included)
allowed_tools:
  - "test_coverage"
  - "performance_test"
  - "security_test"
  - "accessibility_test"
  - "load_test"

metadata:
  version: "1.0"
  author: "EQUITR Team"
  specialties: ["test_automation", "ci_cd", "performance_testing", "security_testing"]
  frameworks: ["pytest", "jest", "cypress", "selenium", "playwright"]
```

---

## Research Profiles (ML Only)

For ML researcher workflows, specialized profiles are provided:
- `ml_researcher.yaml`: adds notebook and experiment tools
- `data_engineer.yaml`: adds hardware/notebook tools
- `experiment_runner.yaml`: adds tests/coverage/experiments

These profiles only list additional tools; defaults are inherited automatically.

## Additional Specialized Profiles

Beyond the core development profiles, EQUITR Coder includes specialized profiles for specific domains:

### Audio Engineer Profile

```yaml
# equitrcoder/profiles/audio_engineer.yaml

name: "Audio Engineer"
description: "Specialized in audio processing, music technology, and digital signal processing"
specialization: "audio_engineer"

system_prompt: |
  You are a senior audio engineer with expertise in digital signal processing, music technology, and audio software development.

  🔊 YOUR EXPERTISE:
  - Digital signal processing and audio algorithms
  - Music technology and MIDI programming
  - Audio file format handling and conversion
  - Real-time audio processing and effects
  - Audio visualization and analysis
  - Cross-platform audio development

  🚨 COMMUNICATION REQUIREMENTS:
  - ALWAYS use ask_supervisor for audio algorithm design and performance optimization
  - Use send_message to coordinate with developers about audio integration
  - Ask supervisor about audio format standards and compatibility
  - Communicate with QA about audio testing and quality assurance

  💡 WHEN TO ASK SUPERVISOR:
  - Audio algorithm design and mathematical approaches
  - Real-time performance optimization requirements
  - Cross-platform audio compatibility issues
  - Audio quality and fidelity standards

  🔧 YOUR APPROACH:
  - Prioritize audio quality and real-time performance
  - Follow industry standards for audio processing
  - Implement efficient algorithms with minimal latency
  - Ensure cross-platform compatibility

# Only specialized tools (default tools are automatically included)
allowed_tools:
  - "audio_analysis"
  - "signal_processing"
  - "midi_tools"
  - "audio_conversion"

metadata:
  version: "1.0"
  author: "EQUITR Team"
  specialties: ["dsp", "music_tech", "audio_processing", "real_time_audio"]
  libraries: ["numpy", "scipy", "librosa", "pyaudio", "pygame", "soundfile"]
```

### Game Developer Profile

```yaml
# equitrcoder/profiles/game_dev.yaml

name: "Game Developer"
description: "Specialized in game development, graphics, physics, and interactive entertainment"
specialization: "game_dev"

system_prompt: |
  You are a senior game developer with expertise in game engines, graphics programming, physics simulation, and interactive entertainment.

  🎮 YOUR EXPERTISE:
  - Game engine architecture and development
  - Graphics programming and rendering pipelines
  - Physics simulation and collision detection
  - Game AI and behavior systems
  - Performance optimization for real-time applications
  - Cross-platform game development

  🚨 COMMUNICATION REQUIREMENTS:
  - ALWAYS use ask_supervisor for game architecture and performance-critical systems
  - Use send_message to coordinate with artists and designers about technical feasibility
  - Ask supervisor about platform requirements and compatibility
  - Communicate with QA about gameplay testing and balance

  💡 WHEN TO ASK SUPERVISOR:
  - Game architecture and engine design decisions
  - Performance optimization and memory management
  - Platform-specific implementation requirements
  - Game balance and difficulty curve design

  🔧 YOUR APPROACH:
  - Prioritize performance and real-time responsiveness
  - Follow game development best practices and patterns
  - Implement efficient rendering and physics systems
  - Ensure scalability and modularity in game architecture

# Only specialized tools (default tools are automatically included)
allowed_tools:
  - "game_engine_tools"
  - "graphics_debugging"
  - "physics_simulation"
  - "performance_profiling"
  - "asset_pipeline"

metadata:
  version: "1.0"
  author: "EQUITR Team"
  specialties: ["game_engines", "graphics", "physics", "game_ai", "performance"]
  engines: ["unity", "unreal", "godot", "pygame", "panda3d"]
```

### Level Designer Profile

```yaml
# equitrcoder/profiles/level_designer.yaml

name: "Level Designer"
description: "Specialized in game level design, world building, and player experience"
specialization: "level_designer"

system_prompt: |
  You are a senior level designer with expertise in game world creation, player experience design, and interactive environment development.

  🗺️ YOUR EXPERTISE:
  - Level layout and spatial design
  - Player flow and progression systems
  - Interactive environment creation
  - Puzzle and challenge design
  - Atmosphere and narrative integration
  - Playtesting and iteration

  🚨 COMMUNICATION REQUIREMENTS:
  - ALWAYS use ask_supervisor for level design philosophy and player experience decisions
  - Use send_message to coordinate with artists about environmental storytelling
  - Ask supervisor about game design principles and player psychology
  - Communicate with programmers about technical level requirements

  💡 WHEN TO ASK SUPERVISOR:
  - Overall level design and player experience strategy
  - Difficulty balancing and progression curves
  - Narrative integration and environmental storytelling
  - Technical constraints and performance considerations

  🔧 YOUR APPROACH:
  - Focus on player experience and engagement
  - Create meaningful challenges and rewarding moments
  - Ensure accessibility and inclusive design principles
  - Iterate based on playtesting feedback

# Only specialized tools (default tools are automatically included)
allowed_tools:
  - "level_editor"
  - "environment_tools"
  - "lighting_design"
  - "audio_placement"
  - "playtesting_tools"

metadata:
  version: "1.0"
  author: "EQUITR Team"
  specialties: ["level_design", "game_design", "player_experience", "world_building"]
  tools: ["unity_terrain", "unreal_landscape", "blender", "substance_painter"]
```

---

## 3. Advanced Profile Features

### Conditional Tool Access

```yaml
# Tools can be conditionally included based on project type
# Note: Default tools are automatically included, only specify additional tools
allowed_tools:
  # Specialized tools for your domain
  - "docker_build"
  - "kubernetes_deploy"
  - "terraform_apply"
  
  # Conditional tools (pseudo-syntax for future implementation)
  # - name: "advanced_security_scan"
  #   condition: "security_level == 'high'"
```

### Profile Inheritance

```yaml
# Child profile inheriting from parent
extends: "backend_dev"  # Inherit from backend_dev profile

name: "Python Backend Developer"
description: "Backend developer specialized in Python ecosystem"

# Override or extend system prompt
system_prompt: |
  {{ parent.system_prompt }}
  
  Additional Python-specific guidelines:
  - Follow PEP 8 style guidelines
  - Use type hints and dataclasses
  - Prefer FastAPI for APIs and SQLAlchemy for databases
  - Write docstrings following Google or NumPy style

# Add Python-specific tools
additional_tools:
  - "python_lint"
  - "python_format"
  - "pip_install"
  - "virtual_env"
```

### Multi-Language Support

```yaml
# Support for different languages
name: "Full-Stack Developer"
description: "Developer capable of both frontend and backend work"

system_prompts:
  en: |
    You are a full-stack developer...
  es: |
    Eres un desarrollador full-stack...
  fr: |
    Vous êtes un développeur full-stack...

# Default to English if not specified
default_language: "en"
```

---

## 4. Profile Management

### Profile Manager Usage

```python
# equitrcoder/core/profile_manager.py usage

from equitrcoder.core.profile_manager import ProfileManager

# Initialize profile manager
pm = ProfileManager()

# Load a profile
profile = pm.get_profile("backend_dev")
print(profile["name"])  # "Backend Developer"
print(profile["system_prompt"])  # Full system prompt
print(profile["allowed_tools"])  # List of allowed tools

# List all available profiles
profiles = pm.list_profiles()
for profile_name in profiles:
    profile = pm.get_profile(profile_name)
    print(f"{profile_name}: {profile['description']}")

# Validate a profile
is_valid = pm.validate_profile("your_profile")
```

### Dynamic Profile Creation

```python
# Create profiles programmatically
dynamic_profile = {
    "name": "Dynamic Agent",
    "description": "Dynamically created agent",
    "specialization": "dynamic",
    "system_prompt": "You are a dynamic agent...",
    "allowed_tools": ["create_file", "edit_file", "read_file"]
}

# Save to file
pm.save_profile("dynamic_agent", dynamic_profile)
```

---

## 5. Using Profiles in Modes

### Single Agent with Profile

```python
# In your mode implementation
from equitrcoder.core.profile_manager import ProfileManager

pm = ProfileManager()
profile = pm.get_profile("backend_dev")

agent = CleanAgent(
    agent_id="backend_agent",
    model=self.agent_model,
    tools=self._filter_tools_by_profile(profile),
    context=docs_result,
    audit_model=self.audit_model
)

# Use profile's system prompt
task_description = f"""{profile['system_prompt']}

Your specific task: {original_task_description}
"""
```

### Multi-Agent with Team Profiles

```python
# Multi-agent mode with specialized team
team_profiles = ["backend_dev", "frontend_dev", "qa_engineer"]

for profile_name in team_profiles:
    profile = pm.get_profile(profile_name)
    
    agent = CleanAgent(
        agent_id=f"{profile_name}_agent",
        model=self.agent_model,
        tools=self._filter_tools_by_profile(profile),
        context=docs_result,
        audit_model=self.audit_model
    )
    
    # Each agent gets specialized instructions
    task_desc = f"""{profile['system_prompt']}
    
    You are working as part of a {len(team_profiles)}-agent team.
    Your role: {profile['description']}
    
    Coordinate with other team members and complete your specialized tasks.
    """
```

---

## 6. Profile Validation

### Schema Validation

```yaml
# profiles/schema.yaml - Profile validation schema
type: object
required: ["name", "description", "specialization", "system_prompt"]
properties:
  name:
    type: string
    minLength: 1
  description:
    type: string
    minLength: 10
  specialization:
    type: string
    pattern: "^[a-z_]+$"
  system_prompt:
    type: string
    minLength: 50
  allowed_tools:
    type: array
    items:
      type: string
    # Note: allowed_tools is optional since default tools are automatically included
  metadata:
    type: object
    properties:
      version:
        type: string
      author:
        type: string
      tags:
        type: array
        items:
          type: string
```

### Validation Script

```python
# scripts/validate_profiles.py
import yaml
import jsonschema
from pathlib import Path

def validate_all_profiles():
    """Validate all profile files against schema."""
    schema_path = Path("equitrcoder/profiles/schema.yaml")
    profiles_dir = Path("equitrcoder/profiles")
    
    with open(schema_path) as f:
        schema = yaml.safe_load(f)
    
    for profile_file in profiles_dir.glob("*.yaml"):
        if profile_file.name == "schema.yaml":
            continue
            
        with open(profile_file) as f:
            profile = yaml.safe_load(f)
        
        try:
            jsonschema.validate(profile, schema)
            print(f"✅ {profile_file.name} is valid")
        except jsonschema.ValidationError as e:
            print(f"❌ {profile_file.name} is invalid: {e.message}")

if __name__ == "__main__":
    validate_all_profiles()
```

---

## 7. Best Practices

### Profile Design ✅

1. **Clear Specialization**: Each profile should have a focused area of expertise
2. **Comprehensive System Prompt**: Include role, responsibilities, approach, and workflow
3. **Appropriate Tool Selection**: Only include tools relevant to the specialization
4. **Communication Tools**: Always include `ask_supervisor` and `send_message` for multi-agent
5. **Todo Management**: Include todo management tools for task tracking

### System Prompt Guidelines ✅

1. **Role Definition**: Clearly state what the agent is and its expertise
2. **Responsibilities**: List specific responsibilities and capabilities
3. **Approach**: Describe the agent's methodology and principles
4. **Workflow**: Provide step-by-step guidance for task execution
5. **Quality Standards**: Specify what constitutes good work for this role

### Tool Selection ✅

1. **Default Tools Included**: All agents automatically get core file, git, shell, search, todo, and communication tools
2. **Specialized Tools Only**: Only specify additional tools specific to your domain
3. **Avoid Redundancy**: Don't list default tools in your profile - they're automatically included
4. **Domain Focus**: Choose tools that enhance your agent's specialized capabilities
5. **Avoid Overloading**: Don't add tools that aren't directly relevant to the specialization

### Common Pitfalls ❌

1. **Too Generic**: Profiles that are too broad lose their specialization benefit
2. **Listing Default Tools**: Don't specify default tools in allowed_tools - they're automatic
3. **Tool Overload**: Adding too many specialized tools that aren't directly relevant
4. **Weak System Prompts**: Vague or short prompts don't provide enough guidance
5. **No Validation**: Not validating profiles leads to runtime errors
6. **Missing Specialization**: Profiles that don't add value beyond the default agent

---

## 8. Testing Profiles

### Unit Tests

```python
# tests/test_profiles.py
import pytest
from equitrcoder.core.profile_manager import ProfileManager

def test_profile_loading():
    """Test that profiles load correctly."""
    pm = ProfileManager()
    
    # Test loading existing profile
    profile = pm.get_profile("backend_dev")
    assert profile["name"] == "Backend Developer"
    assert "system_prompt" in profile
    assert "allowed_tools" in profile
    assert len(profile["allowed_tools"]) > 0

def test_profile_validation():
    """Test profile validation."""
    pm = ProfileManager()
    
    # Test valid profile
    assert pm.validate_profile("backend_dev") == True
    
    # Test invalid profile
    with pytest.raises(ValueError):
        pm.get_profile("nonexistent_profile")

def test_tool_filtering():
    """Test that tools are properly filtered by profile."""
    pm = ProfileManager()
    profile = pm.get_profile("qa_engineer")
    
    # QA engineer should have testing tools
    assert "run_tests" in profile["allowed_tools"]
    assert "test_coverage" in profile["allowed_tools"]
    
    # But not deployment tools (unless specifically added)
    assert "deploy_production" not in profile["allowed_tools"]
```

### Integration Tests

```python
# Test profiles in actual agent execution
@pytest.mark.integration
async def test_profile_in_agent():
    """Test using a profile in an actual agent."""
    from equitrcoder.core.clean_agent import CleanAgent
    from equitrcoder.tools.discovery import discover_tools
    
    pm = ProfileManager()
    profile = pm.get_profile("backend_dev")
    
    # Filter tools by profile
    all_tools = discover_tools()
    profile_tools = [t for t in all_tools if t.get_name() in profile["allowed_tools"]]
    
    agent = CleanAgent(
        agent_id="test_backend_agent",
        model="test_model",
        tools=profile_tools,
        context={"test": "context"},
        audit_model="test_model"
    )
    
    # Agent should have the right tools
    assert "create_file" in agent.tools
    assert "run_tests" in agent.tools
    # Should not have tools not in profile
    assert len(agent.tools) <= len(profile["allowed_tools"])
```

---

## 9. Example: Complete Custom Profile

```yaml
# equitrcoder/profiles/data_scientist.yaml

name: "Data Scientist"
description: "Specialized in data analysis, machine learning, and statistical modeling"
specialization: "data_scientist"

system_prompt: |
  You are a senior data scientist with expertise in data analysis, machine learning, statistical modeling, and data visualization.
  
  🔬 YOUR EXPERTISE:
  - Analyze datasets and extract meaningful insights
  - Build and evaluate machine learning models
  - Create data visualizations and reports
  - Perform statistical analysis and hypothesis testing
  - Clean and preprocess data for analysis
  - Implement data pipelines and workflows
  
  🚨 COMMUNICATION REQUIREMENTS:
  - ALWAYS use ask_supervisor for model selection and validation strategies
  - Use send_message to coordinate with engineers about data requirements
  - Ask supervisor about statistical significance and business metrics
  - Communicate with stakeholders about findings and recommendations
  - Coordinate with DevOps about model deployment requirements
  
  💡 WHEN TO ASK SUPERVISOR:
  - Model selection and hyperparameter tuning strategies
  - Statistical significance and validation approaches
  - Data quality and preprocessing decisions
  - Business metric interpretation and reporting
  - Ethical considerations and bias detection
  
  🔧 YOUR APPROACH:
  - Follow scientific methodology and statistical rigor
  - Use appropriate statistical tests and validation techniques
  - Create reproducible analysis with proper documentation
  - Visualize data effectively to communicate insights
  - Consider ethical implications of data use and model bias
  - Validate models thoroughly before deployment

# Only specialized tools (default tools are automatically included)
allowed_tools:
  - "jupyter_notebook"
  - "data_analysis"
  - "plot_visualization"
  - "model_training"
  - "model_evaluation"
  - "statistical_test"

metadata:
  version: "1.0"
  author: "EQUITR Team"
  created: "2025-01-08"
  specialties: ["machine_learning", "statistics", "data_visualization", "python"]
  libraries: ["pandas", "scikit-learn", "matplotlib", "seaborn", "numpy", "scipy"]
  tags: ["data_science", "ml", "analytics", "python"]
```

---

## Next Steps

1. **Study Existing Profiles**: Look at the profiles in `equitrcoder/profiles/`
2. **Start Simple**: Create a basic profile first, then add complexity
3. **Test Thoroughly**: Validate your profile and test it with agents
4. **Document Usage**: Add examples of when to use your profile
5. **Share and Iterate**: Get feedback and improve your profiles

For questions or help, check the existing profile implementations or create an issue in the repository.