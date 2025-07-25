# Ask Supervisor Tool Guide

## Overview

The `ask_supervisor` tool is a critical component of EQUITR Coder's multi-agent architecture that enables **weak worker agents** to consult with a **strong reasoning supervisor model** for guidance on complex problems. This creates a hierarchical intelligence system where specialized workers can leverage the supervisor's strategic thinking capabilities.

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MULTI-AGENT SYSTEM                      │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐                ┌─────────────────┐    │
│  │   SUPERVISOR    │                │   SUPERVISOR    │    │
│  │  (Strong Model) │◄──ask_supervisor──┤  (Strong Model) │    │
│  │   GPT-4/Claude  │                │   GPT-4/Claude  │    │
│  └─────────────────┘                └─────────────────┘    │
│           │                                   │            │
│           ▼                                   ▼            │
│  ┌─────────────────┐                ┌─────────────────┐    │
│  │ WORKER AGENT 1  │                │ WORKER AGENT 2  │    │
│  │  (Weak Model)   │                │  (Weak Model)   │    │
│  │ GPT-3.5/Smaller │                │ GPT-3.5/Smaller │    │
│  └─────────────────┘                └─────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### When Workers Should Use ask_supervisor

The tool is automatically available to worker agents in multi-agent mode and should be used when:

1. **Complex Architectural Decisions**: Planning system design or major refactoring
2. **Deep Analysis Requirements**: Understanding complex code relationships or dependencies  
3. **Difficult Debugging**: Encountering bugs that require strategic thinking
4. **Implementation Planning**: Deciding between multiple approaches
5. **Strategic Guidance**: Need for project direction or best practices
6. **Edge Cases**: Handling unusual scenarios or requirements

### Tool Parameters

```python
class AskSupervisorArgs(BaseModel):
    question: str = Field(
        ..., description="The question or problem to ask the supervisor"
    )
    context_files: Optional[List[str]] = Field(
        default=None, description="Optional list of file paths to include as context"
    )
    include_repo_tree: bool = Field(
        default=True, description="Include repository tree structure in context"
    )
    include_git_status: bool = Field(
        default=True, description="Include current git status in context"
    )
```

### Context Provided to Supervisor

When a worker calls `ask_supervisor`, the tool automatically gathers:

1. **Repository Structure**: Complete directory tree for understanding project layout
2. **Git Status**: Current changes, staged files, and branch information
3. **Specified Files**: Content of any files explicitly requested for context
4. **Worker's Question**: The specific problem or decision the worker needs help with

### Supervisor Response Framework

The supervisor provides structured guidance following this framework:

#### 1. **Strategic Analysis** (2-3 sentences)
- Core challenge identification
- Key trade-offs and considerations

#### 2. **Recommended Approach** (specific and actionable)
- Clear step-by-step implementation plan
- Specific tools and techniques to use
- Priority order for implementation

#### 3. **Architectural Considerations**
- How the solution fits into the broader codebase
- Patterns and conventions to follow
- Impact on existing code

#### 4. **Risk Assessment**
- Potential issues and mitigation strategies
- Validation approaches
- When to escalate back to supervisor

#### 5. **Next Steps**
- Immediate actions for the worker
- Success criteria and validation points

## Usage Examples

### Example 1: Architectural Decision

```python
# Worker agent encountering complex design decision
await worker.call_tool("ask_supervisor", 
    question="I need to implement user authentication. Should I use JWT tokens, sessions, or OAuth2? The app needs to support both web and mobile clients.",
    context_files=["src/auth.py", "requirements.txt"],
    include_repo_tree=True
)
```

**Supervisor Response:**
```markdown
## STRATEGIC ANALYSIS
You're designing authentication for a multi-client application. The key trade-off is between simplicity (sessions) and scalability/flexibility (JWT/OAuth2).

## RECOMMENDED APPROACH
1. Implement JWT-based authentication for stateless operation
2. Use refresh tokens for security
3. Add OAuth2 support for third-party login
4. Implement middleware for token validation

## ARCHITECTURAL CONSIDERATIONS
- JWT fits well with your existing API structure
- Stateless design supports both web and mobile
- Follow OpenAPI standards for consistent endpoints
- Consider rate limiting and token rotation

## RISK ASSESSMENT
- Risk: JWT token leakage - Mitigate with short expiry times
- Risk: Complex implementation - Start with simple JWT, add OAuth2 later
- Validate with Postman/curl tests before frontend integration

## NEXT STEPS
- Install PyJWT and create auth middleware
- Success criteria: Login/logout working with proper token validation
```

### Example 2: Debugging Assistance

```python
# Worker stuck on a complex bug
await worker.call_tool("ask_supervisor",
    question="I'm getting intermittent database connection errors, but only in production. The error happens randomly every few hours. How should I debug this?",
    context_files=["src/database.py", "docker-compose.yml", "logs/error.log"],
    include_git_status=True
)
```

### Example 3: Code Review and Optimization

```python
# Worker seeking optimization guidance
await worker.call_tool("ask_supervisor",
    question="I've implemented the user search feature, but it's slow with large datasets. Can you review my approach and suggest optimizations?",
    context_files=["src/search.py", "src/models/user.py"],
    include_repo_tree=False  # Not needed for this focused review
)
```

## Configuration and Limits

### Call Limits
- Maximum 5 supervisor calls per worker task by default
- Prevents infinite loops and excessive costs
- Can be configured via worker agent settings

### Cost Management
- Supervisor calls count toward task cost limits
- Each call includes context gathering and response generation
- Monitor usage via tool logging

### Integration with Task Planning

The supervisor naturally integrates with the multi-agent task planning:

1. **Task Breakdown**: Supervisor initially breaks complex requests into worker tasks
2. **Worker Execution**: Workers execute assigned tasks with restricted tools
3. **Consultation**: Workers use `ask_supervisor` when encountering complexity
4. **Coordination**: Supervisor provides guidance that maintains overall project coherence

## Best Practices for Workers

### When to Ask
- **Early**: When planning significant implementations
- **Stuck**: When encountering unexpected complexity
- **Uncertain**: When multiple approaches seem viable
- **Integration**: When changes might affect other parts of the system

### How to Ask Effective Questions
- **Be Specific**: "How should I implement caching?" vs "I need help with performance"
- **Provide Context**: Include relevant files and current state
- **State Constraints**: Mention limitations, requirements, or preferences
- **Ask for Alternatives**: "What are the pros/cons of approaches X vs Y?"

### Don't Overuse
- For simple file operations or basic implementations
- When the path forward is clear and well-defined
- For questions easily answered by documentation

## Monitoring and Analytics

Track supervisor usage through:
- Call frequency per worker
- Question categories and patterns
- Response effectiveness (task completion rates)
- Cost analysis of supervisor vs worker model usage

## Future Enhancements

Planned improvements include:
- **Learning**: Supervisor builds knowledge base from repeated questions
- **Proactive Guidance**: Supervisor suggests consultations based on code patterns
- **Team Coordination**: Multiple workers consulting supervisor simultaneously
- **Domain Specialization**: Different supervisors for different technical domains

---

The `ask_supervisor` tool transforms EQUITR Coder from a collection of independent agents into a truly collaborative system where strategic intelligence guides tactical execution. 