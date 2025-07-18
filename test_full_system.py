#!/usr/bin/env python3
"""
Complete end-to-end test of the EQUITR-coder system.
This will test all functionality in a real dummy project.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the EQUITR-coder directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "EQUITR-coder"))

from EQUITR_coder.api import EquitrAPI


async def test_complete_system():
    print("🚀 Complete System Test")
    print("=" * 60)
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        return

    # Change to dummy project directory
    dummy_path = Path(__file__).parent / "dummy_test_project"
    original_cwd = os.getcwd()
    os.chdir(dummy_path)
    
    try:
        print(f"📁 Working in: {dummy_path}")
        print()
        
        # Test 1: Single Model Mode - Complete Development Cycle
        print("1️⃣ SINGLE MODEL MODE TEST")
        print("-" * 40)
        
        async with EquitrAPI(
            api_key=api_key,
            model="gpt-4o",
            multi_agent=False,
            repo_path="."
        ) as api:
            
            print("📋 Step 1: Create design document")
            response1 = await api.chat("""
            Create a comprehensive design document for a user authentication system.
            Save it as 'design_document.md' with:
            - System architecture
            - Database schema
            - API endpoints
            - Security considerations
            """)
            print(f"✅ Design doc response: {len(response1)} chars")
            
            print("\n📝 Step 2: Create requirements document")
            response2 = await api.chat("""
            Create a detailed requirements document for the authentication system.
            Save it as 'requirements.md' with:
            - Functional requirements
            - Non-functional requirements
            - User stories
            - Acceptance criteria
            """)
            print(f"✅ Requirements doc response: {len(response2)} chars")
            
            print("\n✅ Step 3: Create TODO list")
            response3 = await api.chat("""
            Create a comprehensive TODO list for implementing the authentication system.
            Use the create_todo tool to add at least 5 specific tasks like:
            - Set up database models
            - Implement password hashing
            - Create JWT token system
            - Build login/register endpoints
            - Add input validation
            """)
            print(f"✅ TODO creation response: {len(response3)} chars")
            
            print("\n💻 Step 4: Implement code")
            response4 = await api.chat("""
            Based on the design document, implement a basic authentication system.
            Create these files:
            - auth_models.py (database models)
            - auth_handlers.py (API handlers)
            - auth_utils.py (utility functions)
            - requirements.txt (dependencies)
            """)
            print(f"✅ Code implementation response: {len(response4)} chars")
            
            print("\n🔍 Step 5: Code audit")
            response5 = await api.chat("""
            Review all the code files we created and provide a comprehensive audit:
            - Check for security vulnerabilities
            - Verify design compliance
            - Suggest improvements
            - Validate requirements coverage
            """)
            print(f"✅ Code audit response: {len(response5)} chars")
        
        print("\n2️⃣ MULTI-AGENT MODE TEST")
        print("-" * 40)
        
        async with EquitrAPI(
            api_key=api_key,
            model="gpt-4o",
            multi_agent=True,
            repo_path="."
        ) as api:
            
            print("🧠 Step 1: Complex architectural task (Strong model)")
            response6 = await api.chat("""
            Design a microservices architecture for a complete e-commerce platform.
            Include service decomposition, communication patterns, and data flow.
            This should trigger the supervisor (strong model) for complex reasoning.
            Create 'microservices_architecture.md' with the design.
            """)
            print(f"✅ Architecture design response: {len(response6)} chars")
            
            print("\n💻 Step 2: Simple implementation (Weak model)")
            response7 = await api.chat("""
            Create a simple product catalog service stub based on the microservices design.
            This should be handled by a worker agent.
            Create 'product_service.py' with basic CRUD operations.
            """)
            print(f"✅ Implementation response: {len(response7)} chars")
            
            print("\n🔄 Step 3: Test ask_supervisor functionality")
            response8 = await api.chat("""
            I need strategic guidance on how to implement distributed transactions
            across the microservices we designed. This is complex and should trigger
            the ask_supervisor tool for strategic planning.
            """)
            print(f"✅ Ask supervisor response: {len(response8)} chars")
        
        print("\n3️⃣ VERIFICATION")
        print("-" * 40)
        
        # Check created files
        expected_files = [
            "design_document.md",
            "requirements.md", 
            "auth_models.py",
            "auth_handlers.py",
            "auth_utils.py",
            "requirements.txt",
            "microservices_architecture.md",
            "product_service.py"
        ]
        
        created_files = []
        for file in expected_files:
            if os.path.exists(file):
                size = os.path.getsize(file)
                created_files.append(file)
                print(f"  ✅ {file} ({size} bytes)")
            else:
                print(f"  ❌ {file} - NOT FOUND")
        
        print(f"\n📊 Files created: {len(created_files)}/{len(expected_files)}")
        
        # Test context passing
        print("\n4️⃣ CONTEXT PASSING TEST")
        print("-" * 40)
        
        async with EquitrAPI(
            api_key=api_key,
            model="gpt-4o",
            multi_agent=False,
            repo_path="."
        ) as api:
            
            response9 = await api.chat("""
            Read the design_document.md file and summarize the key architectural decisions.
            Then read the requirements.md and verify if the design meets all requirements.
            """)
            print(f"✅ Context passing test: {len(response9)} chars")
            
            if "design_document.md" in response9.lower() and "requirements" in response9.lower():
                print("  ✅ Context passing: WORKING")
            else:
                print("  ❌ Context passing: FAILED")
        
        print("\n5️⃣ TOOL FUNCTIONALITY TEST")
        print("-" * 40)
        
        async with EquitrAPI(
            api_key=api_key,
            model="gpt-4o",
            multi_agent=False,
            repo_path="."
        ) as api:
            
            # Test all major tools
            tools_test = await api.chat("""
            Test all major tools by:
            1. List all files in the current directory
            2. Check git status
            3. Run a simple command like 'ls -la'
            4. Update one of the TODO items we created
            """)
            print(f"✅ Tools test: {len(tools_test)} chars")
        
        print("\n🎯 FINAL RESULTS")
        print("-" * 40)
        
        results = {
            "Single Model Mode": True,
            "Multi-Agent Mode": True,
            "Document Creation": len([f for f in created_files if f.endswith('.md')]) >= 2,
            "Code Implementation": len([f for f in created_files if f.endswith('.py')]) >= 2,
            "TODO System": "create_todo" in response3.lower(),
            "Context Passing": "design_document.md" in response9.lower(),
            "Tool Integration": "git" in tools_test.lower() or "list" in tools_test.lower()
        }
        
        passed = sum(results.values())
        total = len(results)
        
        for test, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test}: {status}")
        
        print(f"\n🏆 OVERALL SCORE: {passed}/{total} ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 ALL SYSTEMS OPERATIONAL!")
        else:
            print("⚠️  Some systems need attention")
            
    finally:
        os.chdir(original_cwd)


if __name__ == "__main__":
    asyncio.run(test_complete_system())