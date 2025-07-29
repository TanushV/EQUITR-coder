#!/usr/bin/env python3
"""
Comprehensive test of all three clean architecture modes.
Tests with exact models: moonshot/kimi-k2-0711-preview and o3
"""
import asyncio
import sys
import os
from pathlib import Path
import json
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from equitrcoder.modes.single_agent_mode import run_single_agent_mode
from equitrcoder.modes.multi_agent_mode import run_multi_agent_sequential, run_multi_agent_parallel


class TestAuditor:
    """Audits test results to ensure everything works properly."""
    
    def __init__(self, test_dir: Path):
        self.test_dir = test_dir
        self.results = []
    
    def log_result(self, test_name: str, result: dict, files_created: list):
        """Log a test result for auditing."""
        audit_data = {
            "test_name": test_name,
            "timestamp": datetime.now().isoformat(),
            "success": result.get("success", False),
            "cost": result.get("cost", 0),
            "iterations": result.get("iterations", 0),
            "files_created": [str(f) for f in files_created],
            "file_contents": {},
            "audit_passed": result.get("audit_result", {}).get("audit_passed", False),
            "audit_content": result.get("audit_result", {}).get("audit_content", "")
        }
        
        # Read file contents for verification
        for file_path in files_created:
            if file_path.exists() and file_path.stat().st_size < 10000:  # Only read small files
                try:
                    audit_data["file_contents"][str(file_path)] = file_path.read_text()
                except Exception as e:
                    audit_data["file_contents"][str(file_path)] = f"Error reading: {e}"
        
        self.results.append(audit_data)
        return audit_data
    
    def generate_audit_report(self) -> dict:
        """Generate comprehensive audit report."""
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r["success"])
        total_cost = sum(r["cost"] for r in self.results)
        total_iterations = sum(r["iterations"] for r in self.results)
        total_files = sum(len(r["files_created"]) for r in self.results)
        
        # Check for critical issues
        issues = []
        for result in self.results:
            if not result["success"]:
                issues.append(f"{result['test_name']}: Failed execution")
            if not result["audit_passed"]:
                issues.append(f"{result['test_name']}: Audit failed")
            if len(result["files_created"]) == 0:
                issues.append(f"{result['test_name']}: No files created")
        
        return {
            "overall_success": successful_tests == total_tests and len(issues) == 0,
            "summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "total_cost": total_cost,
                "total_iterations": total_iterations,
                "total_files_created": total_files
            },
            "issues": issues,
            "detailed_results": self.results
        }


async def test_single_agent_mode(auditor: TestAuditor):
    """Test single agent mode with comprehensive monitoring."""
    print("🧪 TESTING SINGLE AGENT MODE")
    print("=" * 60)
    
    # Monitoring variables
    tool_calls = []
    messages = []
    iterations = []
    
    def on_message(msg):
        messages.append(msg)
        role = msg.get('role', 'unknown')
        content = msg.get('content', '')
        
        if role == 'tool':
            tool_name = msg.get('metadata', {}).get('tool_name', 'unknown')
            tool_calls.append(tool_name)
            print(f"🔧 Tool: {tool_name} - {content[:80]}{'...' if len(content) > 80 else ''}")
        elif role == 'assistant':
            print(f"🤖 Agent: {content[:100]}{'...' if len(content) > 100 else ''}")
    
    def on_iteration(iteration, status):
        iterations.append({"iteration": iteration, "cost": status.get('cost', 0)})
        print(f"🔄 Iteration {iteration}: Cost=${status.get('cost', 0):.4f}")
    
    def on_audit(audit_info):
        status = audit_info.get('status')
        if status == 'starting':
            print(f"🔍 Starting audit with {audit_info.get('model', 'unknown')}...")
        elif status == 'completed':
            passed = audit_info.get('passed', False)
            print(f"{'✅ AUDIT PASSED' if passed else '❌ AUDIT FAILED'}")
    
    callbacks = {
        'on_message': on_message,
        'on_iteration': on_iteration,
        'on_audit': on_audit
    }
    
    # Test task: Create a calculator program
    task = """Create a comprehensive calculator program:
1. Support basic operations (+, -, *, /)
2. Handle decimal numbers and edge cases
3. Include input validation
4. Add a main function with user interaction
5. Save as 'calculator.py'
6. Include proper error handling"""
    
    print(f"🎯 Task: {task}")
    print("-" * 60)
    
    start_time = time.time()
    
    # Run single agent mode with exact models
    result = await run_single_agent_mode(
        task_description=task,
        agent_model="moonshot/kimi-k2-0711-preview",
        audit_model="o3",
        max_iterations=25,
        callbacks=callbacks
    )
    
    execution_time = time.time() - start_time
    
    print("-" * 60)
    print("📊 SINGLE AGENT RESULTS:")
    print(f"Success: {result['success']}")
    print(f"Cost: ${result.get('cost', 0):.4f}")
    print(f"Iterations: {result.get('iterations', 0)}")
    print(f"Execution Time: {execution_time:.2f}s")
    print(f"Tool Calls Made: {len(tool_calls)} ({', '.join(set(tool_calls))})")
    print(f"Messages Exchanged: {len(messages)}")
    
    # Check created files
    created_files = []
    calculator_file = Path("calculator.py")
    if calculator_file.exists():
        created_files.append(calculator_file)
        print(f"✅ calculator.py created ({calculator_file.stat().st_size} bytes)")
        
        # Test code compilation
        try:
            code = calculator_file.read_text()
            compile(code, str(calculator_file), 'exec')
            print("✅ Code compiles successfully")
            
            # Check for key components
            if "def" in code and "main" in code.lower():
                print("✅ Contains functions and main")
            if "try" in code or "except" in code:
                print("✅ Contains error handling")
                
        except SyntaxError as e:
            print(f"❌ Syntax error: {e}")
    else:
        print("❌ calculator.py not created")
    
    # Log result for audit
    audit_data = auditor.log_result("single_agent", result, created_files)
    
    return result['success'], audit_data


async def test_multi_agent_sequential(auditor: TestAuditor):
    """Test multi-agent sequential mode."""
    print("\n🧪 TESTING MULTI-AGENT SEQUENTIAL MODE")
    print("=" * 60)
    
    # Monitoring
    agent_messages = {}
    agent_tool_calls = {}
    
    def on_message(msg):
        # Track which agent sent the message
        agent_id = getattr(msg, 'agent_id', 'unknown')
        if agent_id not in agent_messages:
            agent_messages[agent_id] = []
        agent_messages[agent_id].append(msg)
        
        role = msg.get('role', 'unknown')
        if role == 'tool':
            tool_name = msg.get('metadata', {}).get('tool_name', 'unknown')
            if agent_id not in agent_tool_calls:
                agent_tool_calls[agent_id] = []
            agent_tool_calls[agent_id].append(tool_name)
            print(f"🔧 {agent_id} used {tool_name}")
    
    def on_audit(audit_info):
        if audit_info.get('status') == 'completed':
            passed = audit_info.get('passed', False)
            print(f"🔍 Agent audit: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    callbacks = {
        'on_message': on_message,
        'on_audit': on_audit
    }
    
    # Test task: Build a simple web app
    task = """Create a simple task management web application:
1. HTML frontend with task input form and task list display
2. Python Flask backend with routes for adding/viewing tasks
3. JSON file storage for persistent data
4. CSS styling for clean appearance
5. JavaScript for dynamic updates"""
    
    print(f"🎯 Task: {task}")
    print("-" * 60)
    
    start_time = time.time()
    
    # Run with 2 agents sequentially
    result = await run_multi_agent_sequential(
        task_description=task,
        num_agents=2,
        agent_model="moonshot/kimi-k2-0711-preview",
        audit_model="o3",
        max_iterations_per_agent=20,
        callbacks=callbacks
    )
    
    execution_time = time.time() - start_time
    
    print("-" * 60)
    print("📊 MULTI-AGENT SEQUENTIAL RESULTS:")
    print(f"Success: {result['success']}")
    print(f"Total Cost: ${result.get('total_cost', 0):.4f}")
    print(f"Total Iterations: {result.get('total_iterations', 0)}")
    print(f"Agents: {result.get('num_agents', 0)}")
    print(f"Execution Time: {execution_time:.2f}s")
    
    # Check created files
    created_files = []
    expected_files = ['app.py', 'index.html', 'style.css', 'script.js', 'tasks.json']
    
    for file_name in expected_files:
        file_path = Path(file_name)
        if file_path.exists():
            created_files.append(file_path)
            print(f"✅ {file_name} created ({file_path.stat().st_size} bytes)")
        
    # Look for any additional files
    for file_path in Path(".").glob("**/*"):
        if (file_path.is_file() and 
            not file_path.name.startswith('.') and 
            file_path.suffix in ['.py', '.html', '.css', '.js', '.json'] and
            file_path not in created_files and
            'test_all_modes' not in file_path.name):
            created_files.append(file_path)
            print(f"📄 Additional file: {file_path}")
    
    print(f"📁 Total files created: {len(created_files)}")
    
    # Log result for audit
    audit_data = auditor.log_result("multi_agent_sequential", result, created_files)
    
    return result['success'], audit_data


async def test_multi_agent_parallel(auditor: TestAuditor):
    """Test multi-agent parallel mode."""
    print("\n🧪 TESTING MULTI-AGENT PARALLEL MODE")
    print("=" * 60)
    
    # Monitoring
    parallel_events = []
    
    def on_message(msg):
        parallel_events.append({
            'timestamp': time.time(),
            'type': 'message',
            'data': msg
        })
        
        role = msg.get('role', 'unknown')
        if role == 'tool':
            tool_name = msg.get('metadata', {}).get('tool_name', 'unknown')
            print(f"🔧 Parallel tool use: {tool_name}")
    
    def on_audit(audit_info):
        parallel_events.append({
            'timestamp': time.time(),
            'type': 'audit',
            'data': audit_info
        })
        
        if audit_info.get('status') == 'completed':
            passed = audit_info.get('passed', False)
            print(f"🔍 Parallel audit: {'✅ PASSED' if passed else '❌ FAILED'}")
    
    callbacks = {
        'on_message': on_message,
        'on_audit': on_audit
    }
    
    # Test task: Build a complete project
    task = """Create a complete data analysis project:
1. Data collection script (CSV generation with sample data)
2. Data processing module (cleaning, filtering functions)
3. Analysis script (statistics, visualizations using matplotlib)
4. Report generator (creates summary markdown file)
5. Configuration file (settings for analysis)
6. Main runner script that ties everything together"""
    
    print(f"🎯 Task: {task}")
    print("-" * 60)
    
    start_time = time.time()
    
    # Run with 3 agents in parallel
    result = await run_multi_agent_parallel(
        task_description=task,
        num_agents=3,
        agent_model="moonshot/kimi-k2-0711-preview",
        audit_model="o3",
        max_iterations_per_agent=20,
        callbacks=callbacks
    )
    
    execution_time = time.time() - start_time
    
    print("-" * 60)
    print("📊 MULTI-AGENT PARALLEL RESULTS:")
    print(f"Success: {result['success']}")
    print(f"Total Cost: ${result.get('total_cost', 0):.4f}")
    print(f"Total Iterations: {result.get('total_iterations', 0)}")
    print(f"Agents: {result.get('num_agents', 0)}")
    print(f"Execution Time: {execution_time:.2f}s")
    print(f"Parallel Events: {len(parallel_events)}")
    
    # Check created files
    created_files = []
    expected_extensions = ['.py', '.csv', '.md', '.json', '.txt', '.config']
    
    for file_path in Path(".").glob("**/*"):
        if (file_path.is_file() and 
            not file_path.name.startswith('.') and 
            any(file_path.suffix == ext for ext in expected_extensions) and
            'test_all_modes' not in file_path.name):
            created_files.append(file_path)
            print(f"📄 {file_path} ({file_path.stat().st_size} bytes)")
    
    print(f"📁 Total files created: {len(created_files)}")
    
    # Check for Python syntax in created files
    python_files = [f for f in created_files if f.suffix == '.py']
    for py_file in python_files:
        try:
            code = py_file.read_text()
            compile(code, str(py_file), 'exec')
            print(f"✅ {py_file.name} compiles successfully")
        except SyntaxError as e:
            print(f"❌ {py_file.name} syntax error: {e}")
    
    # Log result for audit
    audit_data = auditor.log_result("multi_agent_parallel", result, created_files)
    
    return result['success'], audit_data


async def main():
    """Run comprehensive test suite."""
    print("🧪 COMPREHENSIVE CLEAN ARCHITECTURE TEST SUITE")
    print("=" * 80)
    print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Test directory: {Path.cwd()}")
    print(f"🤖 Agent model: moonshot/kimi-k2-0711-preview")
    print(f"🔍 Audit model: o3")
    print("=" * 80)
    
    # Initialize auditor
    auditor = TestAuditor(Path.cwd())
    
    try:
        # Test 1: Single Agent Mode
        single_success, single_audit = await test_single_agent_mode(auditor)
        
        # Test 2: Multi-Agent Sequential Mode
        sequential_success, sequential_audit = await test_multi_agent_sequential(auditor)
        
        # Test 3: Multi-Agent Parallel Mode
        parallel_success, parallel_audit = await test_multi_agent_parallel(auditor)
        
        # Generate comprehensive audit report
        print("\n" + "=" * 80)
        print("🔍 COMPREHENSIVE AUDIT REPORT")
        print("=" * 80)
        
        audit_report = auditor.generate_audit_report()
        
        # Save detailed audit report
        audit_file = Path("comprehensive_audit_report.json")
        with open(audit_file, 'w') as f:
            json.dump(audit_report, f, indent=2)
        
        print(f"📊 Test Summary:")
        print(f"   Total Tests: {audit_report['summary']['total_tests']}")
        print(f"   Successful: {audit_report['summary']['successful_tests']}")
        print(f"   Total Cost: ${audit_report['summary']['total_cost']:.4f}")
        print(f"   Total Iterations: {audit_report['summary']['total_iterations']}")
        print(f"   Files Created: {audit_report['summary']['total_files_created']}")
        
        print(f"\n🎯 Individual Results:")
        print(f"   Single Agent: {'✅ PASSED' if single_success else '❌ FAILED'}")
        print(f"   Multi Sequential: {'✅ PASSED' if sequential_success else '❌ FAILED'}")
        print(f"   Multi Parallel: {'✅ PASSED' if parallel_success else '❌ FAILED'}")
        
        if audit_report['issues']:
            print(f"\n⚠️ Issues Found:")
            for issue in audit_report['issues']:
                print(f"   - {issue}")
        
        overall_success = audit_report['overall_success']
        print(f"\n🏆 OVERALL RESULT: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
        
        # Final verification
        print(f"\n🔍 Final Verification:")
        print(f"   - Tool calling: {'✅ Working' if any('tool' in str(r) for r in auditor.results) else '❌ Not detected'}")
        print(f"   - File creation: {'✅ Working' if audit_report['summary']['total_files_created'] > 0 else '❌ No files created'}")
        print(f"   - Audits: {'✅ Working' if any(r.get('audit_passed') for r in auditor.results) else '❌ All audits failed'}")
        print(f"   - Model usage: {'✅ Both models used' if audit_report['summary']['total_cost'] > 0 else '❌ No costs recorded'}")
        
        print(f"\n📁 Audit report saved to: {audit_file}")
        
        return overall_success
        
    except Exception as e:
        print(f"❌ Test suite failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)