"""
Document Generators for EQUITR Coder

This module contains focused classes for generating different types of documents.
Each generator has a single responsibility for creating one type of document.
All generators implement the standardized IGenerator interface.
"""

import json
from typing import Dict, List, Tuple

from .interfaces import IGenerator, BaseConfigurable
from ..providers.litellm import LiteLLMProvider, Message


class RequirementsGenerator(IGenerator[str], BaseConfigurable):
    """Generates requirements documents from user prompts"""
    
    def __init__(self, model: str = "moonshot/kimi-k2-0711-preview"):
        super().__init__()
        self.model = model
        self.provider = LiteLLMProvider(model=model)
        self._default_config = {
            "model": model,
            "system_prompt_template": """You are a requirements analyst. Your job is to decode the user's prompt into a clear, structured requirements document.

Create a requirements.md document that includes:
1. Project Overview - What the user wants to build
2. Functional Requirements - What the system should do
3. Technical Requirements - How it should be built
4. Success Criteria - How to know when it's complete

Be specific and actionable. Use markdown format."""
        }
    
    async def generate(self, user_prompt: str) -> str:
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
            Message(role="user", content=f"User prompt: {user_prompt}"),
        ]

        response = await self.provider.chat(messages=messages)
        return response.content
    
    async def generate_interactive(self, user_prompt: str, interaction_callback) -> Tuple[str, List[Dict[str, str]]]:
        """Interactive requirements creation with back-and-forth discussion."""
        conversation_log = []

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
                            "description": "The complete requirements document in markdown format",
                        }
                    },
                    "required": ["requirements_content"],
                },
            },
        }

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=f"I want to build: {user_prompt}"),
        ]

        while True:
            response = await self.provider.chat(messages=messages, tools=[finalize_tool])
            
            conversation_log.append(
                {"role": "assistant", "content": response.content or "Processing..."}
            )

            if response.tool_calls:
                for tool_call in response.tool_calls:
                    if tool_call.function["name"] == "finalize_requirements":
                        args = json.loads(tool_call.function["arguments"])
                        return args["requirements_content"], conversation_log

            if interaction_callback:
                user_response = await interaction_callback("AI", response.content)
                if user_response is None or user_response.lower() in ["quit", "exit", "done"]:
                    final_req = await self.generate(user_prompt)
                    return final_req, conversation_log

                messages.append(Message(role="assistant", content=response.content))
                messages.append(Message(role="user", content=user_response))
                conversation_log.append({"role": "user", "content": user_response})
            else:
                final_req = await self.generate(user_prompt)
                return final_req, conversation_log


class DesignGenerator(IGenerator[str], BaseConfigurable):
    """Generates design documents from requirements"""
    
    def __init__(self, model: str = "moonshot/kimi-k2-0711-preview"):
        super().__init__()
        self.model = model
        self.provider = LiteLLMProvider(model=model)
        self._default_config = {
            "model": model,
            "system_prompt_template": """You are a system designer. Your job is to create a technical design document based on the requirements.

Create a design.md document that includes:
1. System Architecture - High-level structure
2. Components - What parts need to be built
3. Data Flow - How information moves through the system
4. Implementation Plan - Step-by-step approach
5. File Structure - What files/directories will be created

Be technical and specific. Use markdown format."""
        }
    
    async def generate(self, user_prompt: str, requirements: str) -> str:
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
            Message(
                role="user",
                content=f"User prompt: {user_prompt}\n\nRequirements:\n{requirements}",
            ),
        ]

        response = await self.provider.chat(messages=messages)
        return response.content
    
    async def generate_interactive(self, user_prompt: str, requirements: str, interaction_callback) -> Tuple[str, List[Dict[str, str]]]:
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
                            "description": "The complete design document in markdown format",
                        }
                    },
                    "required": ["design_content"],
                },
            },
        }

        messages = [
            Message(role="system", content=system_prompt),
            Message(
                role="user",
                content=f"Original request: {user_prompt}\n\nRequirements we agreed on:\n{requirements}",
            ),
        ]

        while True:
            response = await self.provider.chat(messages=messages, tools=[finalize_tool])

            conversation_log.append(
                {"role": "assistant", "content": response.content or "Processing..."}
            )

            if response.tool_calls:
                for tool_call in response.tool_calls:
                    if tool_call.function["name"] == "finalize_design":
                        args = json.loads(tool_call.function["arguments"])
                        return args["design_content"], conversation_log

            if interaction_callback:
                user_response = await interaction_callback("AI", response.content)
                if user_response is None or user_response.lower() in ["quit", "exit", "done"]:
                    final_design = await self.generate(user_prompt, requirements)
                    return final_design, conversation_log

                messages.append(Message(role="assistant", content=response.content))
                messages.append(Message(role="user", content=user_response))
                conversation_log.append({"role": "user", "content": user_response})
            else:
                final_design = await self.generate(user_prompt, requirements)
                return final_design, conversation_log


class TodosGenerator(IGenerator[str], BaseConfigurable):
    """Generates todos documents from requirements and design"""
    
    def __init__(self, model: str = "moonshot/kimi-k2-0711-preview"):
        super().__init__()
        self.model = model
        self.provider = LiteLLMProvider(model=model)
        self._default_config = {
            "model": model,
            "max_categories": 6,
            "min_categories": 3,
            "max_tasks_per_category": 8,
            "min_tasks_per_category": 2
        }
    
    async def generate(self, user_prompt: str, requirements: str, design: str) -> str:
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
                            "description": "Name of the category (e.g., 'Setup & Configuration', 'Core Implementation')",
                        },
                        "tasks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "title": {
                                        "type": "string",
                                        "description": "Clear, actionable task title",
                                    },
                                    "description": {
                                        "type": "string",
                                        "description": "Detailed description of what needs to be done",
                                    },
                                    "can_work_parallel": {
                                        "type": "boolean",
                                        "description": "Whether this task can be worked on simultaneously with other tasks in the category",
                                    },
                                },
                                "required": ["title", "description", "can_work_parallel"],
                            },
                            "description": "List of tasks in this category",
                        },
                    },
                    "required": ["category_name", "tasks"],
                },
            },
        }

        messages = [
            Message(role="system", content=system_prompt),
            Message(
                role="user",
                content=f"User prompt: {user_prompt}\n\nRequirements:\n{requirements}\n\nDesign:\n{design}",
            ),
        ]

        categories = []

        while True:
            response = await self.provider.chat(messages=messages, tools=[create_todo_tool])

            if response.tool_calls:
                for tool_call in response.tool_calls:
                    if tool_call.function["name"] == "create_todo_category":
                        args = json.loads(tool_call.function["arguments"])
                        categories.append(args)

                        tool_calls_dict = [
                            {"id": tc.id, "type": tc.type, "function": tc.function}
                            for tc in response.tool_calls
                        ]
                        messages.append(
                            Message(
                                role="assistant",
                                content=response.content or "",
                                tool_calls=tool_calls_dict,
                            )
                        )
                        messages.append(
                            Message(
                                role="tool",
                                content=f"Created category: {args['category_name']} with {len(args['tasks'])} tasks",
                                tool_call_id=tool_call.id,
                            )
                        )
            else:
                break

        # Generate markdown from collected categories
        todos_content = "# Project Tasks\n\n"

        for category in categories:
            todos_content += f"## {category['category_name']}\n"
            for task in category["tasks"]:
                parallel_note = (
                    " (can work in parallel)"
                    if task.get("can_work_parallel", False)
                    else ""
                )
                todos_content += f"- [ ] {task['title']}{parallel_note}\n"
                if task.get("description") and task["description"] != task["title"]:
                    todos_content += f"  - {task['description']}\n"
            todos_content += "\n"

        return todos_content
    
    async def generate_interactive(self, user_prompt: str, requirements: str, design: str, interaction_callback) -> Tuple[str, List[Dict[str, str]]]:
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
                            "description": "The complete todos document in markdown format with checkbox format",
                        }
                    },
                    "required": ["todos_content"],
                },
            },
        }

        messages = [
            Message(role="system", content=system_prompt),
            Message(
                role="user",
                content=f"Original request: {user_prompt}\n\nRequirements:\n{requirements}\n\nDesign:\n{design}",
            ),
        ]

        while True:
            response = await self.provider.chat(messages=messages, tools=[finalize_tool])

            conversation_log.append(
                {"role": "assistant", "content": response.content or "Processing..."}
            )

            if response.tool_calls:
                for tool_call in response.tool_calls:
                    if tool_call.function["name"] == "finalize_todos":
                        args = json.loads(tool_call.function["arguments"])
                        return args["todos_content"], conversation_log

            if interaction_callback:
                user_response = await interaction_callback("AI", response.content)
                if user_response is None or user_response.lower() in ["quit", "exit", "done"]:
                    final_todos = await self.generate(user_prompt, requirements, design)
                    return final_todos, conversation_log

                messages.append(Message(role="assistant", content=response.content))
                messages.append(Message(role="user", content=user_response))
                conversation_log.append({"role": "user", "content": user_response})
            else:
                final_todos = await self.generate(user_prompt, requirements, design)
                return final_todos, conversation_log