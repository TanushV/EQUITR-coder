"""
Document Creation Workflow System

This module implements the mandatory 3-document creation workflow:
1. Requirements document (decode prompt into what is needed)
2. Design document (system design of what should be implemented)
3. Todos document (task breakdown)

The workflow differs by mode:
- TUI mode: Back-and-forth discussion with user
- Programmatic mode: AI creates them automatically
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

from ..providers.litellm import LiteLLMProvider, Message
from ..tools.builtin.todo import TodoManager


@dataclass
class DocumentCreationResult:
    """Result of document creation process."""
    success: bool
    requirements_path: Optional[str] = None
    design_path: Optional[str] = None
    todos_path: Optional[str] = None
    error: Optional[str] = None
    conversation_log: List[Dict[str, str]] = None


class DocumentWorkflowManager:
    """Manages the 3-document creation workflow."""
    
    def __init__(self, model: str = "moonshot/kimi-k2-0711-preview"):
        # Auto-load environment variables
        from ..utils.env_loader import auto_load_environment
        auto_load_environment()
        
        self.model = model
        self.provider = LiteLLMProvider(model=model)
        self.todo_manager = TodoManager()
        
    async def create_documents_programmatic(
        self, 
        user_prompt: str, 
        project_path: str = "."
    ) -> DocumentCreationResult:
        """
        Create all 3 documents automatically for programmatic mode.
        AI decides everything without user interaction.
        """
        try:
            project_path = Path(project_path)
            docs_dir = project_path / "docs"
            docs_dir.mkdir(exist_ok=True)
            
            # Step 1: Create requirements document
            print("🔍 Creating requirements document...")
            requirements_content = await self._generate_requirements(user_prompt)
            requirements_path = docs_dir / "requirements.md"
            requirements_path.write_text(requirements_content)
            
            # Step 2: Create design document
            print("🏗️ Creating design document...")
            design_content = await self._generate_design(user_prompt, requirements_content)
            design_path = docs_dir / "design.md"
            design_path.write_text(design_content)
            
            # Step 3: Create todos document
            print("📋 Creating todos document...")
            todos_content = await self._generate_todos(user_prompt, requirements_content, design_content)
            todos_path = docs_dir / "todos.md"
            todos_path.write_text(todos_content)
            
            # Step 4: Parse todos and create them in the todo system
            print("📝 Parsing and creating todos in the system...")
            await self._parse_and_create_todos(todos_content)
            
            return DocumentCreationResult(
                success=True,
                requirements_path=str(requirements_path),
                design_path=str(design_path),
                todos_path=str(todos_path)
            )
            
        except Exception as e:
            return DocumentCreationResult(
                success=False,
                error=str(e)
            )
    
    async def create_documents_interactive(
        self, 
        user_prompt: str, 
        project_path: str = ".",
        interaction_callback=None
    ) -> DocumentCreationResult:
        """
        Create all 3 documents through interactive discussion for TUI mode.
        AI and user discuss back and forth until completion.
        """
        try:
            project_path = Path(project_path)
            docs_dir = project_path / "docs"
            docs_dir.mkdir(exist_ok=True)
            
            conversation_log = []
            
            # Step 1: Interactive requirements creation
            print("🔍 Starting interactive requirements discussion...")
            requirements_content, req_log = await self._interactive_requirements(
                user_prompt, interaction_callback
            )
            conversation_log.extend(req_log)
            
            requirements_path = docs_dir / "requirements.md"
            requirements_path.write_text(requirements_content)
            
            # Step 2: Interactive design creation
            print("🏗️ Starting interactive design discussion...")
            design_content, design_log = await self._interactive_design(
                user_prompt, requirements_content, interaction_callback
            )
            conversation_log.extend(design_log)
            
            design_path = docs_dir / "design.md"
            design_path.write_text(design_content)
            
            # Step 3: Interactive todos creation
            print("📋 Starting interactive todos discussion...")
            todos_content, todos_log = await self._interactive_todos(
                user_prompt, requirements_content, design_content, interaction_callback
            )
            conversation_log.extend(todos_log)
            
            todos_path = docs_dir / "todos.md"
            todos_path.write_text(todos_content)
            
            # Step 4: Parse todos and create them in the todo system
            await self._parse_and_create_todos(todos_content)
            
            return DocumentCreationResult(
                success=True,
                requirements_path=str(requirements_path),
                design_path=str(design_path),
                todos_path=str(todos_path),
                conversation_log=conversation_log
            )
            
        except Exception as e:
            return DocumentCreationResult(
                success=False,
                error=str(e)
            )
    
    async def _generate_requirements(self, user_prompt: str) -> str:
        """Generate requirements document automatically."""
        system_prompt = """You are a requirements analyst. Your job is to decode the user's prompt into a clear, structured requirements document.

Create a requirements.md document that includes:
1. Project Overview - What the user wants to build
2. Functional Requirements - What the system should do
3. Technical Requirements - How it should be built
4. Success Criteria - How to know when it's complete

Be specific and actionable. Use markdown format."""

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=f"User prompt: {user_prompt}")
        ]
        
        response = await self.provider.chat(messages=messages)
        return response.content
    
    async def _generate_design(self, user_prompt: str, requirements: str) -> str:
        """Generate design document automatically."""
        system_prompt = """You are a system designer. Your job is to create a technical design document based on the requirements.

Create a design.md document that includes:
1. System Architecture - High-level structure
2. Components - What parts need to be built
3. Data Flow - How information moves through the system
4. Implementation Plan - Step-by-step approach
5. File Structure - What files/directories will be created

Be technical and specific. Use markdown format."""

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=f"User prompt: {user_prompt}\n\nRequirements:\n{requirements}")
        ]
        
        response = await self.provider.chat(messages=messages)
        return response.content
    
    async def _generate_todos(self, user_prompt: str, requirements: str, design: str) -> str:
        """Generate todos document automatically."""
        system_prompt = """You are a project manager. Your job is to break down the design into specific, actionable tasks.

Create a todos.md document that includes:
1. A numbered list of specific tasks
2. Each task should be clear and actionable
3. Tasks should be in logical order
4. Include file creation, coding, testing tasks
5. Use checkbox format: - [ ] Task description

Be specific about what files to create and what code to write. Use markdown format."""

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=f"User prompt: {user_prompt}\n\nRequirements:\n{requirements}\n\nDesign:\n{design}")
        ]
        
        response = await self.provider.chat(messages=messages)
        return response.content
    
    async def _interactive_requirements(
        self, 
        user_prompt: str, 
        interaction_callback
    ) -> Tuple[str, List[Dict[str, str]]]:
        """Interactive requirements creation with back-and-forth discussion."""
        conversation_log = []
        
        # Start the conversation
        system_prompt = """You are a requirements analyst having a discussion with a user to understand their needs.

Your goal is to create a comprehensive requirements document through back-and-forth discussion.

Rules:
1. Ask clarifying questions about unclear aspects
2. Suggest improvements or considerations they might have missed
3. When you have enough information, use the function call to finalize requirements
4. Be conversational and helpful
5. Focus on understanding WHAT they want to build, not HOW

Available functions:
- finalize_requirements: Call this when you have enough information to create the final requirements document"""

        # Define the finalize function
        finalize_tool = {
            "type": "function",
            "function": {
                "name": "finalize_requirements",
                "description": "Finalize the requirements document when enough information has been gathered",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "requirements_content": {
                            "type": "string",
                            "description": "The complete requirements document in markdown format"
                        }
                    },
                    "required": ["requirements_content"]
                }
            }
        }
        
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=f"I want to build: {user_prompt}")
        ]
        
        while True:
            # AI response
            response = await self.provider.chat(messages=messages, tools=[finalize_tool])
            
            # Log AI message
            conversation_log.append({
                "role": "assistant",
                "content": response.content or "Processing..."
            })
            
            # Check if AI wants to finalize
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    if tool_call.function['name'] == 'finalize_requirements':
                        args = json.loads(tool_call.function['arguments'])
                        return args['requirements_content'], conversation_log
            
            # Show AI message to user and get response
            if interaction_callback:
                user_response = await interaction_callback("AI", response.content)
                if user_response is None or user_response.lower() in ['quit', 'exit', 'done']:
                    # User wants to stop - generate final requirements
                    final_req = await self._generate_requirements(user_prompt)
                    return final_req, conversation_log
                
                # Add user response to conversation
                messages.append(Message(role="assistant", content=response.content))
                messages.append(Message(role="user", content=user_response))
                conversation_log.append({
                    "role": "user", 
                    "content": user_response
                })
            else:
                # No callback - auto-finalize
                final_req = await self._generate_requirements(user_prompt)
                return final_req, conversation_log
    
    async def _interactive_design(
        self, 
        user_prompt: str, 
        requirements: str, 
        interaction_callback
    ) -> Tuple[str, List[Dict[str, str]]]:
        """Interactive design creation with back-and-forth discussion."""
        conversation_log = []
        
        system_prompt = """You are a system designer discussing the technical design with a user.

Your goal is to create a comprehensive design document through back-and-forth discussion.

Rules:
1. Ask about technical preferences and constraints
2. Suggest architecture options and get feedback
3. Discuss implementation approaches
4. When you have enough information, use the function call to finalize design
5. Focus on HOW to build what was specified in requirements

Available functions:
- finalize_design: Call this when you have enough information to create the final design document"""

        finalize_tool = {
            "type": "function",
            "function": {
                "name": "finalize_design",
                "description": "Finalize the design document when enough information has been gathered",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "design_content": {
                            "type": "string",
                            "description": "The complete design document in markdown format"
                        }
                    },
                    "required": ["design_content"]
                }
            }
        }
        
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=f"Original request: {user_prompt}\n\nRequirements we agreed on:\n{requirements}")
        ]
        
        while True:
            response = await self.provider.chat(messages=messages, tools=[finalize_tool])
            
            conversation_log.append({
                "role": "assistant",
                "content": response.content or "Processing..."
            })
            
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    if tool_call.function['name'] == 'finalize_design':
                        args = json.loads(tool_call.function['arguments'])
                        return args['design_content'], conversation_log
            
            if interaction_callback:
                user_response = await interaction_callback("AI", response.content)
                if user_response is None or user_response.lower() in ['quit', 'exit', 'done']:
                    final_design = await self._generate_design(user_prompt, requirements)
                    return final_design, conversation_log
                
                messages.append(Message(role="assistant", content=response.content))
                messages.append(Message(role="user", content=user_response))
                conversation_log.append({
                    "role": "user",
                    "content": user_response
                })
            else:
                final_design = await self._generate_design(user_prompt, requirements)
                return final_design, conversation_log
    
    async def _interactive_todos(
        self, 
        user_prompt: str, 
        requirements: str, 
        design: str, 
        interaction_callback
    ) -> Tuple[str, List[Dict[str, str]]]:
        """Interactive todos creation with back-and-forth discussion."""
        conversation_log = []
        
        system_prompt = """You are a project manager discussing the task breakdown with a user.

Your goal is to create a comprehensive todos document through back-and-forth discussion.

Rules:
1. Ask about task priorities and preferences
2. Suggest task breakdown and get feedback
3. Discuss implementation order
4. When you have enough information, use the function call to finalize todos
5. Focus on breaking down the design into specific actionable tasks

Available functions:
- finalize_todos: Call this when you have enough information to create the final todos document"""

        finalize_tool = {
            "type": "function",
            "function": {
                "name": "finalize_todos",
                "description": "Finalize the todos document when enough information has been gathered",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "todos_content": {
                            "type": "string",
                            "description": "The complete todos document in markdown format with checkbox format"
                        }
                    },
                    "required": ["todos_content"]
                }
            }
        }
        
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=f"Original request: {user_prompt}\n\nRequirements:\n{requirements}\n\nDesign:\n{design}")
        ]
        
        while True:
            response = await self.provider.chat(messages=messages, tools=[finalize_tool])
            
            conversation_log.append({
                "role": "assistant",
                "content": response.content or "Processing..."
            })
            
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    if tool_call.function['name'] == 'finalize_todos':
                        args = json.loads(tool_call.function['arguments'])
                        return args['todos_content'], conversation_log
            
            if interaction_callback:
                user_response = await interaction_callback("AI", response.content)
                if user_response is None or user_response.lower() in ['quit', 'exit', 'done']:
                    final_todos = await self._generate_todos(user_prompt, requirements, design)
                    return final_todos, conversation_log
                
                messages.append(Message(role="assistant", content=response.content))
                messages.append(Message(role="user", content=user_response))
                conversation_log.append({
                    "role": "user",
                    "content": user_response
                })
            else:
                final_todos = await self._generate_todos(user_prompt, requirements, design)
                return final_todos, conversation_log
    
    async def _parse_and_create_todos(self, todos_content: str):
        """Parse the todos document and create todos in the system."""
        print(f"📝 Parsing todos content (length: {len(todos_content)} chars)")
        lines = todos_content.split('\n')
        print(f"📝 Found {len(lines)} lines in todos document")
        
        todo_count = 0
        for i, line in enumerate(lines):
            line = line.strip()
            # Look for checkbox format: - [ ] Task description
            if line.startswith('- [ ]'):
                task_description = line[5:].strip()  # Remove '- [ ] '
                if task_description:
                    try:
                        todo = self.todo_manager.create_todo(
                            title=task_description,
                            description=f"Auto-generated from todos document",
                            priority="medium",
                            tags=["auto-generated"],
                            assignee=None
                        )
                        print(f"✅ Created todo {todo_count + 1}: {todo.id} - {task_description}")
                        todo_count += 1
                    except Exception as e:
                        print(f"❌ Warning: Could not create todo '{task_description}': {e}")
                else:
                    print(f"⚠️ Empty task description on line {i + 1}: '{line}'")
            elif line and not line.startswith('#') and not line.startswith('##'):
                # Show non-empty, non-header lines that don't match the pattern
                print(f"🔍 Line {i + 1} doesn't match todo pattern: '{line}'")
        
        print(f"📝 Total todos created: {todo_count}")
        
        # Verify todos were created
        all_todos = self.todo_manager.list_todos()
        print(f"📝 Total todos in system: {len(all_todos)}")
        for todo in all_todos[-todo_count:]:  # Show the last created todos
            print(f"  - {todo.status}: {todo.title}")
    
    async def create_split_todos_for_parallel_agents(
        self, 
        user_prompt: str, 
        requirements_content: str,
        design_content: str,
        num_agents: int,
        project_path: str = "."
    ) -> List[str]:
        """
        Create split todos documents for parallel agents.
        Each agent gets the same requirements.md and design.md, but different todos.
        
        Returns list of todos file paths for each agent.
        """
        try:
            project_path = Path(project_path)
            docs_dir = project_path / "docs"
            docs_dir.mkdir(exist_ok=True)
            
            # First generate the complete todos
            complete_todos = await self._generate_todos(user_prompt, requirements_content, design_content)
            
            # Parse todos into individual tasks
            todo_lines = []
            for line in complete_todos.split('\n'):
                line = line.strip()
                if line.startswith('- [ ]'):
                    todo_lines.append(line)
            
            if not todo_lines:
                raise Exception("No todos found to split among agents")
            
            # Split todos among agents
            todos_per_agent = len(todo_lines) // num_agents
            remainder = len(todo_lines) % num_agents
            
            agent_todo_files = []
            start_idx = 0
            
            for agent_idx in range(num_agents):
                # Calculate how many todos this agent gets
                agent_todo_count = todos_per_agent + (1 if agent_idx < remainder else 0)
                end_idx = start_idx + agent_todo_count
                
                # Get todos for this agent
                agent_todos = todo_lines[start_idx:end_idx]
                
                # Create todos document for this agent
                agent_todos_content = f"""# Todos for Agent {agent_idx + 1}

## Assigned Tasks
{chr(10).join(agent_todos)}

## Instructions
- You are Agent {agent_idx + 1} of {num_agents}
- Complete ALL assigned todos above
- You cannot finish until ALL your todos are marked as completed
- Use the update_todo tool to mark todos as completed when done
- Read the requirements.md and design.md files for context
- Work systematically through each todo
"""
                
                # Save to file
                agent_todos_path = docs_dir / f"todos_agent_{agent_idx + 1}.md"
                agent_todos_path.write_text(agent_todos_content)
                agent_todo_files.append(str(agent_todos_path))
                
                # Create todos in the system for this agent
                for todo_line in agent_todos:
                    task_description = todo_line[5:].strip()  # Remove '- [ ] '
                    if task_description:
                        try:
                            self.todo_manager.create_todo(
                                title=task_description,
                                description=f"Assigned to Agent {agent_idx + 1}",
                                priority="medium",
                                tags=["auto-generated", f"agent-{agent_idx + 1}"],
                                assignee=f"agent_{agent_idx + 1}"
                            )
                        except Exception as e:
                            print(f"Warning: Could not create todo '{task_description}': {e}")
                
                start_idx = end_idx
            
            return agent_todo_files
            
        except Exception as e:
            print(f"Error creating split todos: {e}")
            return []