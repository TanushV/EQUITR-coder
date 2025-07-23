"""
Documentation Generator for EQUITR Coder

Generates mandatory documentation (requirements, design, todos) based on
conversational planning sessions.
"""

import json
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..providers.openrouter import Message


class DocumentationGenerator:
    """Generates project documentation from planning conversations."""

    def __init__(self, provider, repo_path: str):
        self.provider = provider
        self.repo_path = Path(repo_path)

    async def generate_all_documents(
        self, conversation: List[Dict[str, str]]
    ) -> Optional[Dict[str, str]]:
        """Generate all three MANDATORY documents from conversation history - NO EXCEPTIONS."""
        try:
            # Create consolidated conversation context
            conversation_text = self._format_conversation(conversation)

            # Generate requirements document - MANDATORY
            requirements = await self._generate_requirements(conversation_text)
            if not requirements or not requirements.strip():
                raise Exception(
                    "CRITICAL: Requirements document generation failed - this is MANDATORY"
                )

            # Generate design document - MANDATORY
            design = await self._generate_design(conversation_text, requirements)
            if not design or not design.strip():
                raise Exception(
                    "CRITICAL: Design document generation failed - this is MANDATORY"
                )

            # Generate todo list - MANDATORY
            todos = await self._generate_todos(conversation_text, requirements, design)
            if not todos or not todos.strip():
                raise Exception(
                    "CRITICAL: Todo list generation failed - this is MANDATORY"
                )

            # VALIDATION: Ensure all three documents have substantial content
            min_length = 100  # Minimum characters for a valid document
            if len(requirements.strip()) < min_length:
                raise Exception(
                    f"CRITICAL: Requirements document too short ({len(requirements)} chars) - must be comprehensive"
                )
            if len(design.strip()) < min_length:
                raise Exception(
                    f"CRITICAL: Design document too short ({len(design)} chars) - must be comprehensive"
                )
            if len(todos.strip()) < min_length:
                raise Exception(
                    f"CRITICAL: Todo list too short ({len(todos)} chars) - must be comprehensive"
                )

            # Save documents to files - MANDATORY
            await self._save_documents(requirements, design, todos)

            # Final validation that all documents were created
            docs_result = {
                "requirements": requirements,
                "design": design,
                "todos": todos,
            }

            # Double-check all documents exist and have content
            for doc_type, content in docs_result.items():
                if not content or not content.strip():
                    raise Exception(
                        f"CRITICAL: {doc_type} document is empty - ALL THREE DOCUMENTS ARE MANDATORY"
                    )

            print("✅ Successfully generated ALL THREE MANDATORY documents")
            return docs_result

        except Exception as e:
            print(f"❌ CRITICAL ERROR generating MANDATORY documentation: {e}")
            # Do not return partial results - ALL THREE DOCUMENTS ARE MANDATORY
            return None

    async def generate_documents_iteratively(
        self, conversation: List[Dict[str, str]], feedback_callback=None
    ) -> Optional[Dict[str, str]]:
        """Generate documents iteratively with user feedback and revisions."""
        max_iterations = 3
        current_iteration = 0

        while current_iteration < max_iterations:
            print(
                f"\n📋 Generating documentation (iteration {current_iteration + 1}/{max_iterations})..."
            )

            # Generate initial or revised documents
            if current_iteration == 0:
                docs = await self.generate_all_documents(conversation)
            else:
                # Regenerate with feedback
                docs = await self._regenerate_with_feedback(
                    conversation, feedback_history
                )

            if not docs:
                print("❌ Failed to generate documentation")
                return None

            # If no feedback callback provided, return documents
            if not feedback_callback:
                return docs

            # Get user feedback
            print("\n📋 Generated Documentation:")
            for doc_type, content in docs.items():
                print(f"\n=== {doc_type.upper()} ===")
                print(content[:500] + "..." if len(content) > 500 else content)

            feedback = feedback_callback(docs)

            if feedback["action"] == "approve":
                print("✅ Documentation approved!")
                return docs
            elif feedback["action"] == "revise":
                print("📝 Incorporating feedback...")
                if current_iteration == 0:
                    feedback_history = []
                feedback_history.append(feedback)
                current_iteration += 1
            else:  # quit
                print("❌ Documentation generation cancelled")
                return None

        print("⚠️ Maximum iterations reached, returning last version")
        return docs

    async def _regenerate_with_feedback(
        self, conversation: List[Dict[str, str]], feedback_history: List[Dict]
    ) -> Optional[Dict[str, str]]:
        """Regenerate documents incorporating user feedback."""
        try:
            conversation_text = self._format_conversation(conversation)

            # Build feedback context
            feedback_context = "\nUSER FEEDBACK FROM PREVIOUS ITERATIONS:\n"
            for i, feedback in enumerate(feedback_history):
                feedback_context += f"\nIteration {i + 1} Feedback:\n"
                feedback_context += f"Changes requested: {feedback.get('changes', 'No specific changes')}\n"
                if feedback.get("specific_feedback"):
                    for doc_type, doc_feedback in feedback["specific_feedback"].items():
                        feedback_context += f"- {doc_type}: {doc_feedback}\n"

            # Generate requirements with feedback
            requirements = await self._generate_requirements_with_feedback(
                conversation_text, feedback_context, feedback_history
            )
            if not requirements or not requirements.strip():
                raise Exception(
                    "CRITICAL: Requirements document generation with feedback failed"
                )

            # Generate design with feedback
            design = await self._generate_design_with_feedback(
                conversation_text, requirements, feedback_context, feedback_history
            )
            if not design or not design.strip():
                raise Exception(
                    "CRITICAL: Design document generation with feedback failed"
                )

            # Generate todos with feedback
            todos = await self._generate_todos_with_feedback(
                conversation_text,
                requirements,
                design,
                feedback_context,
                feedback_history,
            )
            if not todos or not todos.strip():
                raise Exception("CRITICAL: Todo list generation with feedback failed")

            # Save updated documents
            await self._save_documents(requirements, design, todos)

            return {"requirements": requirements, "design": design, "todos": todos}

        except Exception as e:
            print(f"❌ ERROR regenerating documentation with feedback: {e}")
            return None

    async def _generate_requirements_with_feedback(
        self,
        conversation_text: str,
        feedback_context: str,
        feedback_history: List[Dict],
    ) -> Optional[str]:
        """Generate requirements document incorporating user feedback."""
        prompt = f"""
Based on the following planning conversation and user feedback, generate a comprehensive requirements document.

CONVERSATION:
{conversation_text}

{feedback_context}

INSTRUCTIONS:
- Carefully incorporate all user feedback from previous iterations
- Address specific concerns and requested changes
- Maintain comprehensive coverage while addressing feedback
- Generate a detailed requirements document that includes:

1. PROJECT OVERVIEW
   - Brief description of the project
   - Main objectives and goals

2. FUNCTIONAL REQUIREMENTS
   - Core features and functionality
   - User stories or use cases
   - Input/output specifications

3. NON-FUNCTIONAL REQUIREMENTS
   - Performance requirements
   - Security considerations
   - Scalability needs
   - Technology constraints

4. ACCEPTANCE CRITERIA
   - Definition of done
   - Success metrics
   - Testing requirements

Make the document comprehensive and actionable. Focus on clarity and completeness while addressing all user feedback.
"""

        messages = [Message(role="user", content=prompt)]
        response = await self.provider.chat(messages, temperature=0.1)
        return response.content.strip() if response.content else None

    async def _generate_design_with_feedback(
        self,
        conversation_text: str,
        requirements: str,
        feedback_context: str,
        feedback_history: List[Dict],
    ) -> Optional[str]:
        """Generate design document incorporating user feedback."""
        prompt = f"""
Based on the requirements and user feedback, generate a comprehensive design document.

REQUIREMENTS:
{requirements}

CONVERSATION:
{conversation_text}

{feedback_context}

INSTRUCTIONS:
- Carefully incorporate all user feedback from previous iterations
- Address specific design concerns and requested changes
- Ensure design aligns with updated requirements
- Generate a detailed design document that includes:

1. SYSTEM ARCHITECTURE
   - High-level system overview
   - Component breakdown
   - Data flow diagrams

2. TECHNICAL DESIGN
   - Technology stack
   - Database schema (if applicable)
   - API specifications (if applicable)
   - File structure

3. USER INTERFACE DESIGN (if applicable)
   - Screen layouts
   - User workflows
   - Navigation structure

4. IMPLEMENTATION STRATEGY
   - Development phases
   - Dependencies and prerequisites
   - Risk mitigation

Make the design detailed and implementable while addressing all user feedback.
"""

        messages = [Message(role="user", content=prompt)]
        response = await self.provider.chat(messages, temperature=0.1)
        return response.content.strip() if response.content else None

    async def _generate_todos_with_feedback(
        self,
        conversation_text: str,
        requirements: str,
        design: str,
        feedback_context: str,
        feedback_history: List[Dict],
    ) -> Optional[str]:
        """Generate todo list incorporating user feedback."""
        prompt = f"""
Based on the requirements, design, and user feedback, generate a comprehensive todo list.

REQUIREMENTS:
{requirements}

DESIGN:
{design}

CONVERSATION:
{conversation_text}

{feedback_context}

INSTRUCTIONS:
- Carefully incorporate all user feedback from previous iterations
- Address specific task-related concerns and requested changes
- Ensure todos align with updated requirements and design
- Generate a detailed, prioritized todo list that includes:

1. SETUP AND PREPARATION
   - Environment setup
   - Dependency installation
   - Initial project structure

2. CORE IMPLEMENTATION
   - Feature development tasks
   - Component implementation
   - Integration tasks

3. TESTING AND VALIDATION
   - Unit testing
   - Integration testing
   - User acceptance testing

4. DEPLOYMENT AND FINALIZATION
   - Deployment preparation
   - Documentation updates
   - Final testing

Each todo should be:
- Specific and actionable
- Properly prioritized
- Include estimated effort/complexity
- Have clear acceptance criteria

Make the todo list comprehensive and implementable while addressing all user feedback.
"""

        messages = [Message(role="user", content=prompt)]
        response = await self.provider.chat(messages, temperature=0.1)
        return response.content.strip() if response.content else None

    def _format_conversation(self, conversation: List[Dict[str, str]]) -> str:
        """Format conversation history into readable text."""
        formatted = []
        for msg in conversation:
            role = msg["role"].upper()
            content = msg["content"]
            formatted.append(f"{role}: {content}")
        return "\n\n".join(formatted)

    async def _generate_requirements(self, conversation_text: str) -> Optional[str]:
        """Generate requirements document from conversation."""
        prompt = f"""
Based on the following planning conversation, generate a comprehensive requirements document.

CONVERSATION:
{conversation_text}

Generate a detailed requirements document that includes:

1. PROJECT OVERVIEW
   - Brief description of the project
   - Main objectives and goals

2. FUNCTIONAL REQUIREMENTS
   - Core features and functionality
   - User stories or use cases
   - Input/output specifications

3. NON-FUNCTIONAL REQUIREMENTS
   - Performance requirements
   - Security considerations
   - Scalability needs
   - Compatibility requirements

4. TECHNICAL CONSTRAINTS
   - Technology stack preferences
   - Platform requirements
   - Dependencies and integrations

5. ACCEPTANCE CRITERIA
   - Success metrics
   - Testing requirements
   - Quality standards

Format the document in clear markdown with appropriate headings and bullet points.
Be specific and comprehensive based on the conversation details.
"""

        try:
            response = await self.provider.chat(
                messages=[Message(role="user", content=prompt)],
                temperature=0.3,
                max_tokens=2000,
            )
            return response.content
        except Exception as e:
            print(f"Error generating requirements: {e}")
            return None

    async def _generate_design(
        self, conversation_text: str, requirements: str
    ) -> Optional[str]:
        """Generate design document from conversation and requirements."""
        prompt = f"""
Based on the planning conversation and requirements document, generate a comprehensive design document.

CONVERSATION:
{conversation_text}

REQUIREMENTS:
{requirements}

Generate a detailed design document that includes:

1. SYSTEM ARCHITECTURE
   - High-level architecture overview
   - Component breakdown
   - Data flow diagrams (described in text)

2. TECHNICAL DESIGN
   - Technology stack selection and rationale
   - Database schema (if applicable)
   - API design (if applicable)
   - File structure and organization

3. COMPONENT SPECIFICATIONS
   - Individual component descriptions
   - Interfaces and interactions
   - Data structures and models

4. IMPLEMENTATION STRATEGY
   - Development phases
   - Priority order of components
   - Risk mitigation strategies

5. TESTING STRATEGY
   - Unit testing approach
   - Integration testing plan
   - Testing tools and frameworks

6. DEPLOYMENT CONSIDERATIONS
   - Environment requirements
   - Configuration management
   - Deployment strategy

Format the document in clear markdown with appropriate headings and detailed explanations.
Be specific about implementation details and architectural decisions.
"""

        try:
            response = await self.provider.chat(
                messages=[Message(role="user", content=prompt)],
                temperature=0.3,
                max_tokens=2500,
            )
            return response.content
        except Exception as e:
            print(f"Error generating design: {e}")
            return None

    async def _generate_todos(
        self, conversation_text: str, requirements: str, design: str
    ) -> Optional[str]:
        """Generate todo list from conversation, requirements, and design."""
        prompt = f"""
Based on the planning conversation, requirements, and design documents, generate a comprehensive todo list.

CONVERSATION:
{conversation_text}

REQUIREMENTS:
{requirements}

DESIGN:
{design}

Generate a detailed todo list that includes:

1. SETUP TASKS
   - Project initialization
   - Environment setup
   - Dependencies installation

2. CORE IMPLEMENTATION TASKS
   - Break down each major component into specific tasks
   - Order tasks by dependencies and priority
   - Include estimated complexity (Simple/Medium/Complex)

3. TESTING TASKS
   - Unit test creation
   - Integration test setup
   - Test data preparation

4. DOCUMENTATION TASKS
   - Code documentation
   - User documentation
   - API documentation (if applicable)

5. DEPLOYMENT TASKS
   - Configuration setup
   - Deployment preparation
   - Production readiness checks

Format as a numbered list with clear, actionable items.
Each task should be specific enough to be completed independently.
Group related tasks together and indicate dependencies where relevant.
Include priority levels (High/Medium/Low) for each task.
"""

        try:
            response = await self.provider.chat(
                messages=[Message(role="user", content=prompt)],
                temperature=0.3,
                max_tokens=2000,
            )
            return response.content
        except Exception as e:
            print(f"Error generating todos: {e}")
            return None

    async def _save_documents(self, requirements: str, design: str, todos: str) -> None:
        """Save generated documents to files."""
        try:
            # Create docs directory if it doesn't exist
            docs_dir = self.repo_path / "docs"
            docs_dir.mkdir(exist_ok=True)

            # Save requirements document
            (docs_dir / "requirements.md").write_text(requirements, encoding="utf-8")

            # Save design document
            (docs_dir / "design.md").write_text(design, encoding="utf-8")

            # Save todo list
            (docs_dir / "todos.md").write_text(todos, encoding="utf-8")

            print(f"📁 Documents saved to {docs_dir}")

        except Exception as e:
            print(f"Error saving documents: {e}")

    def get_existing_documents(self) -> Optional[Dict[str, str]]:
        """Load existing documentation - ALL THREE DOCUMENTS ARE MANDATORY."""
        try:
            docs_dir = self.repo_path / "docs"
            if not docs_dir.exists():
                print(
                    "❌ CRITICAL: No docs directory found - ALL THREE DOCUMENTS ARE MANDATORY"
                )
                return None

            docs = {}
            required_files = {
                "requirements": "requirements.md",
                "design": "design.md",
                "todos": "todos.md",
            }

            missing_files = []
            empty_files = []

            # Load all three MANDATORY documents
            for doc_type, filename in required_files.items():
                file_path = docs_dir / filename
                if not file_path.exists():
                    missing_files.append(filename)
                else:
                    content = file_path.read_text(encoding="utf-8")
                    if not content.strip():
                        empty_files.append(filename)
                    else:
                        docs[doc_type] = content

            # VALIDATION: All three documents must exist and have content
            if missing_files:
                print(
                    f"❌ CRITICAL: Missing MANDATORY documentation files: {', '.join(missing_files)}"
                )
                return None

            if empty_files:
                print(
                    f"❌ CRITICAL: Empty MANDATORY documentation files: {', '.join(empty_files)}"
                )
                return None

            # Final validation - ensure all three documents are present
            if len(docs) != 3:
                print(
                    f"❌ CRITICAL: Expected 3 documents, found {len(docs)}. ALL THREE ARE MANDATORY."
                )
                return None

            # Validate document content length
            min_length = 50  # Minimum characters for a valid document
            for doc_type, content in docs.items():
                if len(content.strip()) < min_length:
                    print(
                        f"❌ CRITICAL: {doc_type} document too short ({len(content)} chars) - must be comprehensive"
                    )
                    return None

            print("✅ All three MANDATORY documents loaded successfully")
            return docs

        except Exception as e:
            print(f"❌ CRITICAL ERROR loading MANDATORY documents: {e}")
            return None
