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
    
    def __init__(self, model: str = "moonshot/kimi-k2-0711-preview", todo_file: str = None):
        # Auto-load environment variables
        from ..utils.env_loader import auto_load_environment
        auto_load_environment()
        
        self.model = model
        self.provider = LiteLLMProvider(model=model)
        self.todo_manager = TodoManager(todo_file=todo_file)
        
    async def create_documents_programmatic(
        self, 
        user_prompt: str, 
        project_path: str = ".",
        task_name: str = None
    ) -> DocumentCreationResult:
        """
        Create all 3 documents automatically for programmatic mode.
        AI decides everything without user interaction.
        Creates isolated folder for each task.
        """
        try:
            project_path = Path(project_path)
            
            # Create unique task folder
            if not task_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                task_name = f"task_{timestamp}"
            
            # Create task-specific docs directory
            docs_dir = project_path / "docs" / task_name
            docs_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"📁 Creating documents in: {docs_dir}")
            
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
            await self._parse_and_create_todos(todos_content, task_name)
            
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
        interaction_callback=None,
        task_name: str = None
    ) -> DocumentCreationResult:
        """
        Create all 3 documents through interactive discussion for TUI mode.
        AI and user discuss back and forth until completion.
        Creates isolated folder for each task.
        """
        try:
            project_path = Path(project_path)
            
            # Create unique task folder
            if not task_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                task_name = f"task_{timestamp}"
            
            # Create task-specific docs directory
            docs_dir = project_path / "docs" / task_name
            docs_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"📁 Creating documents in: {docs_dir}")
            
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
            await self._parse_and_create_todos(todos_content, task_name)
            
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
        """Generate todos document automatically with grouped, reasonable tasks using tool calls."""
        system_prompt = """You are a project manager creating a well-organized task breakdown for potential parallel execution.

CRITICAL REQUIREMENTS:
1. Create 1-25 tasks total (flexible based on project complexity)
2. Group tasks into 3-6 logical categories for easy parallel agent distribution
3. Each category should be self-contained and independent
4. Tasks within categories should be related and sequential
5. Use clear, actionable descriptions
6. You can work on multiple todos at once if they're related

WORKFLOW:
1. Analyze the requirements and design
2. Create logical categories for parallel agent distribution
3. Use the create_todo_category tool to create each category with its tasks
4. Each category should have 2-8 tasks that can be worked on by one agent
5. Categories should have minimal dependencies on each other

RULES FOR PARALLEL AGENT DISTRIBUTION:
- Each category should be assignable to a separate agent
- Categories should have minimal dependencies on each other
- Aim for 3-6 categories to allow 2-6 parallel agents
- Tasks should be specific and actionable
- Focus on what needs to be delivered, not how to do it
- Multiple related tasks can be worked on simultaneously

Available tools:
- create_todo_category: Use this to create each category with its associated tasks"""

        # Define the create_todo_category tool
        create_todo_tool = {
            "type": "function",
            "function": {
                "name": "create_todo_category",
                "description": "Create a category of related todos for parallel agent execution",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "category_name": {
                            "type": "string",
                            "description": "Name of the category (e.g., 'Setup & Configuration', 'Core Implementation')"
                        },
                        "tasks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {
                                        "type": "string",
                                        "description": "Clear, actionable task title"
                                    },
                                    "description": {
                                        "type": "string",
                                        "description": "Detailed description of what needs to be done"
                                    },
                                    "can_work_parallel": {
                                        "type": "boolean",
                                        "description": "Whether this task can be worked on simultaneously with other tasks in the category"
                                    }
                                },
                                "required": ["title", "description", "can_work_parallel"]
                            },
                            "description": "List of tasks in this category"
                        }
                    },
                    "required": ["category_name", "tasks"]
                }
            }
        }

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=f"User prompt: {user_prompt}\n\nRequirements:\n{requirements}\n\nDesign:\n{design}")
        ]
        
        # Collect all categories and tasks
        categories = []
        
        while True:
            response = await self.provider.chat(messages=messages, tools=[create_todo_tool])
            
            if response.tool_calls:
                for tool_call in response.tool_calls:
                    if tool_call.function['name'] == 'create_todo_category':
                        args = json.loads(tool_call.function['arguments'])
                        categories.append(args)
                        
                        # Add tool response to continue conversation
                        tool_calls_dict = [{"id": tc.id, "type": tc.type, "function": tc.function} for tc in response.tool_calls]
                        messages.append(Message(role="assistant", content=response.content or "", tool_calls=tool_calls_dict))
                        messages.append(Message(role="tool", content=f"Created category: {args['category_name']} with {len(args['tasks'])} tasks", tool_call_id=tool_call.id))
            else:
                # No more tool calls, we're done
                break
        
        # Generate markdown from collected categories
        todos_content = "# Project Tasks\n\n"
        
        for category in categories:
            todos_content += f"## {category['category_name']}\n"
            for task in category['tasks']:
                parallel_note = " (can work in parallel)" if task.get('can_work_parallel', False) else ""
                todos_content += f"- [ ] {task['title']}{parallel_note}\n"
                if task.get('description') and task['description'] != task['title']:
                    todos_content += f"  - {task['description']}\n"
            todos_content += "\n"
        
        return todos_content
    
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
    
    async def _parse_and_create_todos(self, todos_content: str, task_folder: str = None):
        """Parse the todos document and create todos only for this specific task."""
        print(f"📝 Parsing todos content (length: {len(todos_content)} chars)")
        lines = todos_content.split('\n')
        print(f"📝 Found {len(lines)} lines in todos document")
        
        # Clear existing todos for this task to prevent compounding
        if task_folder:
            existing_todos = self.todo_manager.list_todos()
            task_todos = [t for t in existing_todos if task_folder in t.tags]
            for todo in task_todos:
                self.todo_manager.delete_todo(todo.id)
            print(f"🧹 Cleared {len(task_todos)} existing todos for task: {task_folder}")
        
        todo_count = 0
        for i, line in enumerate(lines):
            line = line.strip()
            # Look for checkbox format: - [ ] Task description
            if line.startswith('- [ ]'):
                task_description = line[5:].strip()  # Remove '- [ ] '
                if task_description:
                    try:
                        tags = ["auto-generated"]
                        if task_folder:
                            tags.append(f"task-{task_folder}")
                        
                        todo = self.todo_manager.create_todo(
                            title=task_description,
                            description=f"Auto-generated from todos document for task: {task_folder or 'unknown'}",
                            priority="medium",
                            tags=tags,
                            assignee=None
                        )
                        print(f"✅ Created todo {todo_count + 1}: {todo.id} - {task_description}")
                        todo_count += 1
                    except Exception as e:
                        print(f"❌ Warning: Could not create todo '{task_description}': {e}")
                else:
                    print(f"⚠️ Empty task description on line {i + 1}: '{line}'")
        
        print(f"📝 Total todos created for this task: {todo_count}")
        
        # Show only todos for this specific task
        if task_folder:
            task_todos = [t for t in self.todo_manager.list_todos() if f"task-{task_folder}" in t.tags]
            print(f"📝 Todos for task '{task_folder}': {len(task_todos)}")
            for todo in task_todos:
                print(f"  - {todo.status}: {todo.title}")
        else:
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
        Each agent gets complete categories of todos, not individual todos.
        
        Returns list of todos file paths for each agent.
        """
        try:
            project_path = Path(project_path)
            docs_dir = project_path / "docs"
            docs_dir.mkdir(exist_ok=True)
            
            # Generate todos with categorized structure
            system_prompt = """You are a project manager creating a categorized task breakdown for parallel agents.

Create a todos.md document with clear categories that can be distributed among multiple agents.
Each category should be a complete, self-contained set of related tasks.

Format:
# Project Todos

## Category 1: [Category Name]
- [ ] Task 1 for this category
- [ ] Task 2 for this category
- [ ] Task 3 for this category

## Category 2: [Category Name]  
- [ ] Task 1 for this category
- [ ] Task 2 for this category

## Category 3: [Category Name]
- [ ] Task 1 for this category
- [ ] Task 2 for this category

Make sure each category is independent and can be worked on by a separate agent.
Create at least as many categories as there will be agents.
Use clear, descriptive category names like "Setup & Configuration", "Core Implementation", "Testing & Validation", etc."""

            from ..providers.litellm import LiteLLMProvider, Message
            provider = LiteLLMProvider(model=self.model)
            
            messages = [
                Message(role="system", content=system_prompt),
                Message(role="user", content=f"User prompt: {user_prompt}\n\nRequirements:\n{requirements_content}\n\nDesign:\n{design_content}\n\nNumber of agents: {num_agents}")
            ]
            
            response = await provider.chat(messages=messages)
            complete_todos = response.content
            
            # Parse todos into categories
            categories = []
            current_category = None
            current_todos = []
            
            for line in complete_todos.split('\n'):
                line = line.strip()
                if line.startswith('## '):
                    # Save previous category
                    if current_category and current_todos:
                        categories.append({
                            'name': current_category,
                            'todos': current_todos.copy()
                        })
                    # Start new category
                    current_category = line[3:].strip()  # Remove '## '
                    current_todos = []
                elif line.startswith('- [ ]'):
                    if current_category:
                        current_todos.append(line)
            
            # Save last category
            if current_category and current_todos:
                categories.append({
                    'name': current_category,
                    'todos': current_todos.copy()
                })
            
            if not categories:
                raise Exception("No categorized todos found to split among agents")
            
            print(f"📋 Found {len(categories)} categories: {[cat['name'] for cat in categories]}")
            
            # Distribute categories among agents
            agent_todo_files = []
            
            for agent_idx in range(num_agents):
                # Assign categories to this agent (round-robin distribution)
                agent_categories = []
                for cat_idx, category in enumerate(categories):
                    if cat_idx % num_agents == agent_idx:
                        agent_categories.append(category)
                
                if not agent_categories:
                    # If no categories assigned, create a coordination category
                    agent_categories = [{
                        'name': 'Coordination & Integration',
                        'todos': ['- [ ] Coordinate with other agents and integrate their work']
                    }]
                
                # Create todos document for this agent
                agent_todos_content = f"""# Todos for Agent {agent_idx + 1}

## Assigned Categories
Agent {agent_idx + 1} is responsible for the following categories:

"""
                
                for category in agent_categories:
                    agent_todos_content += f"## {category['name']}\n"
                    for todo in category['todos']:
                        agent_todos_content += f"{todo}\n"
                    agent_todos_content += "\n"
                
                agent_todos_content += f"""## Instructions
- You are Agent {agent_idx + 1} of {num_agents}
- Complete ALL todos in your assigned categories above
- Each category is a complete, self-contained set of related tasks
- You cannot finish until ALL your todos are marked as completed
- Use communication tools to coordinate with other agents
- Read the requirements.md and design.md files for context
- Work systematically through each category
"""
                
                # Save to file
                agent_todos_path = docs_dir / f"todos_agent_{agent_idx + 1}.md"
                agent_todos_path.write_text(agent_todos_content)
                agent_todo_files.append(str(agent_todos_path))
                
                print(f"📋 Agent {agent_idx + 1} assigned categories: {[cat['name'] for cat in agent_categories]}")
                
                # Create todos in the system for this agent
                for category in agent_categories:
                    for todo_line in category['todos']:
                        task_description = todo_line[5:].strip()  # Remove '- [ ] '
                        if task_description:
                            try:
                                self.todo_manager.create_todo(
                                    title=task_description,
                                    description=f"Category: {category['name']} - Assigned to Agent {agent_idx + 1}",
                                    priority="medium",
                                    tags=["auto-generated", f"agent-{agent_idx + 1}", category['name'].lower().replace(' ', '-')],
                                    assignee=f"agent_{agent_idx + 1}"
                                )
                            except Exception as e:
                                print(f"Warning: Could not create todo '{task_description}': {e}")
            
            return agent_todo_files
            
        except Exception as e:
            print(f"Error creating split todos: {e}")
            return []