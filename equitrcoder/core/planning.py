"""
Conversational Planning Module - Strong AI for requirements gathering
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from ..providers.litellm import LiteLLMProvider
from ..providers.openrouter import Message


class ConversationalPlanner:
    """Strong AI for conversational planning and requirements gathering"""

    def __init__(self, provider: LiteLLMProvider, repo_path: str):
        self.provider = provider
        self.repo_path = Path(repo_path)
        self.conversation_history: List[Dict[str, str]] = []
        self.planning_complete = False

    async def start_planning_conversation(self, initial_prompt: str) -> bool:
        """
        Start conversational planning with user
        Returns True if planning completed successfully, False if user exited
        """
        print("\n🎯 CONVERSATIONAL PLANNING PHASE")
        print("=" * 50)
        print("Strong AI will discuss requirements with you.")
        print("Type '/done' when satisfied, '/exit' to quit planning.")
        print("-" * 50)

        # Initial system prompt for strong AI
        system_prompt = """You are a senior software architect conducting a detailed planning session.

Your role is to:
1. Ask clarifying questions to fully understand requirements
2. Identify edge cases and potential issues
3. Gather detailed specifications
4. Ensure nothing is missed
5. Continue asking questions until you have comprehensive understanding

Be thorough and methodical. Don't proceed until you're confident you understand all aspects.

Current project context: {initial_prompt}

Ask your first clarifying question.""".format(
            initial_prompt=initial_prompt
        )

        self.conversation_history = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": initial_prompt},
        ]

        exchange_count = 0

        while (
            not self.planning_complete and exchange_count < 20
        ):  # Limit to prevent infinite loops
            try:
                # Get AI's next question/response
                ai_response = await self._get_ai_response()
                print(f"\n🤖 AI: {ai_response}")

                # Get user input
                user_input = input("\n👤 You: ").strip()

                if user_input.lower() in ["/exit", "/quit", "/q"]:
                    print("\n❌ Planning session cancelled by user")
                    return False
                elif user_input.lower() in ["/done", "/complete", "/finish"]:
                    print("\n✅ Planning session completed by user")
                    self.planning_complete = True
                    break
                elif user_input.lower() == "/skip":
                    print("\n⏭️  Skipping planning conversation")
                    return True

                self.conversation_history.append(
                    {"role": "user", "content": user_input}
                )
                exchange_count += 1

            except KeyboardInterrupt:
                print("\n\n❌ Planning session interrupted")
                return False

        if exchange_count >= 20:
            print(
                "\n⚠️  Maximum exchanges reached. Proceeding with available information."
            )

        return True

    async def _get_ai_response(self) -> str:
        """Get response from strong AI model"""
        try:
            messages = [
                Message(role=msg["role"], content=msg["content"])
                for msg in self.conversation_history
            ]

            response = await self.provider.chat(
                messages=messages, temperature=0.7, max_tokens=400
            )

            ai_content = response.content.strip()
            self.conversation_history.append(
                {"role": "assistant", "content": ai_content}
            )
            return ai_content

        except Exception as e:
            return f"Error getting AI response: {str(e)}. Please provide your input."

    async def generate_planning_documents(self) -> Dict[str, str]:
        """Generate requirements, design docs, and todo list from conversation"""
        if not self.conversation_complete():
            return {}

        print("\n📋 Generating Planning Documents...")

        # Build context from conversation
        conversation_context = "\n".join(
            [
                f"{msg['role'].upper()}: {msg['content']}"
                for msg in self.conversation_history
                if msg["role"] != "system"
            ]
        )

        # Generate requirements document
        requirements = await self._generate_requirements_doc(conversation_context)

        # Generate design document
        design = await self._generate_design_doc(conversation_context, requirements)

        # Generate todo list
        todos = await self._generate_todo_list(
            conversation_context, requirements, design
        )

        # Save documents
        docs_dir = self.repo_path / "planning_docs"
        docs_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        files = {
            "requirements": docs_dir / f"requirements_{timestamp}.md",
            "design": docs_dir / f"design_{timestamp}.md",
            "todos": docs_dir / f"todos_{timestamp}.json",
        }

        files["requirements"].write_text(requirements)
        files["design"].write_text(design)
        files["todos"].write_text(json.dumps(todos, indent=2))

        print(f"✅ Planning documents saved to {docs_dir}")

        return {
            "requirements": requirements,
            "design": design,
            "todos": json.dumps(todos, indent=2),
            "files": {k: str(v) for k, v in files.items()},
        }

    async def _generate_requirements_doc(self, context: str) -> str:
        """Generate comprehensive requirements document"""
        prompt = f"""
Based on this planning conversation:

{context}

Create a comprehensive REQUIREMENTS DOCUMENT with:

1. FUNCTIONAL REQUIREMENTS
   - Detailed feature specifications
   - User stories with acceptance criteria
   - Business logic requirements
   - Data requirements

2. NON-FUNCTIONAL REQUIREMENTS
   - Performance requirements
   - Security requirements
   - Scalability requirements
   - Usability requirements

3. TECHNICAL REQUIREMENTS
   - Technology stack specifications
   - Integration requirements
   - API requirements
   - Database requirements

4. CONSTRAINTS & ASSUMPTIONS
   - Technical constraints
   - Business constraints
   - Assumptions made

Format as a clear, detailed markdown document.
"""

        messages = [Message(role="user", content=prompt)]
        response = await self.provider.chat(messages=messages, max_tokens=1000)
        return response.content

    async def _generate_design_doc(self, context: str, requirements: str) -> str:
        """Generate detailed design document"""
        prompt = f"""
Based on:
- Planning conversation: {context}
- Requirements: {requirements}

Create a comprehensive DESIGN DOCUMENT with:

1. SYSTEM ARCHITECTURE
   - High-level architecture diagram description
   - Component breakdown
   - Data flow

2. FILE STRUCTURE
   - Directory structure
   - File organization
   - Naming conventions

3. IMPLEMENTATION PLAN
   - Files to be created
   - Files to be modified
   - Files to be deleted
   - Code structure for each component

4. DATABASE DESIGN
   - Schema design
   - Table structures
   - Relationships

5. API DESIGN
   - Endpoint specifications
   - Request/response formats
   - Authentication methods

6. ERROR HANDLING STRATEGY
   - Error types and handling
   - Validation approaches
   - Logging strategy

Format as a detailed markdown document with specific file paths and code structure.
"""

        messages = [Message(role="user", content=prompt)]
        response = await self.provider.chat(messages=messages, max_tokens=1500)
        return response.content

    async def _generate_todo_list(
        self, context: str, requirements: str, design: str
    ) -> List[Dict[str, Any]]:
        """Generate structured todo list"""
        prompt = f"""
Based on:
- Planning: {context}
- Requirements: {requirements}
- Design: {design}

Create a structured TODO LIST as JSON with:
[
  {{
    "id": "unique-id",
    "title": "Task title",
    "description": "Detailed description",
    "priority": "high|medium|low",
    "estimated_hours": 2,
    "dependencies": ["other-task-ids"],
    "files_affected": ["specific/file/paths"],
    "type": "create|modify|delete|test|setup"
  }}
]

Include ALL tasks needed to implement the design, in dependency order.
"""

        messages = [Message(role="user", content=prompt)]
        response = await self.provider.chat(messages=messages, max_tokens=1000)

        try:
            # Clean JSON response
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]

            todos = json.loads(content)
            return todos if isinstance(todos, list) else []
        except Exception:
            return [
                {
                    "id": "1",
                    "title": "Implement basic structure",
                    "description": "Start implementation",
                    "priority": "high",
                    "type": "create",
                }
            ]

    def conversation_complete(self) -> bool:
        """Check if planning conversation is complete"""
        return self.planning_complete or len(self.conversation_history) > 2

    def get_conversation_summary(self) -> str:
        """Get summary of planning conversation"""
        return "\n".join(
            [
                f"{msg['role']}: {msg['content'][:100]}..."
                for msg in self.conversation_history[-6:]
                if msg["role"] != "system"
            ]
        )
