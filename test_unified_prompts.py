#!/usr/bin/env python3
"""
Test that the unified system prompts are working correctly.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from equitrcoder.modes.single_agent_mode import SingleAgentMode
from equitrcoder.modes.multi_agent_mode import MultiAgentMode
from pathlib import Path
import yaml

def test_unified_prompts():
    """Test that the unified system prompts are working correctly."""
    print("🧪 Testing Unified System Prompts...")
    
    # Test 1: Check system_prompt.yaml has both prompts
    print("\n1. Testing unified system prompt configuration...")
    config_path = Path('equitrcoder/config/system_prompt.yaml')
    
    if config_path.exists():
        print("   ✅ system_prompt.yaml exists")
        
        with open(config_path, 'r') as f:
            system_config = yaml.safe_load(f)
        
        expected_prompts = ['single_agent_prompt', 'multi_agent_prompt', 'requirements_analyst_prompt', 'system_designer_prompt', 'project_manager_prompt']
        for prompt_name in expected_prompts:
            if prompt_name in system_config:
                prompt_length = len(system_config[prompt_name])
                print(f"   ✅ {prompt_name}: {prompt_length} chars")
            else:
                print(f"   ❌ {prompt_name}: missing")
                return False
    else:
        print("   ❌ system_prompt.yaml not found")
        return False
    
    # Test 2: Verify mode_prompts.yaml is deleted
    print("\n2. Testing mode_prompts.yaml is removed...")
    mode_prompts_path = Path('equitrcoder/config/mode_prompts.yaml')
    
    if not mode_prompts_path.exists():
        print("   ✅ mode_prompts.yaml successfully removed")
    else:
        print("   ❌ mode_prompts.yaml still exists (should be deleted)")
        return False
    
    # Test 3: Test SingleAgentMode loads unified prompts
    print("\n3. Testing SingleAgentMode with unified prompts...")
    try:
        single_mode = SingleAgentMode(
            agent_model="test_model",
            orchestrator_model="test_model", 
            audit_model="test_model",
            max_cost=None,
            max_iterations=None,
            auto_commit=False
        )
        
        prompts = single_mode.system_prompts
        if 'single_agent_prompt' in prompts:
            prompt = prompts['single_agent_prompt']
            print(f"   ✅ Single-agent prompt loaded: {len(prompt)} chars")
            
            # Check for key elements
            if 'SINGLE-AGENT MISSION' in prompt:
                print("   ✅ Contains single-agent mission statement")
            else:
                print("   ❌ Missing single-agent mission statement")
                return False
                
            if 'ask_supervisor' in prompt and 'MANDATORY SUPERVISOR CONSULTATION' in prompt:
                print("   ✅ Contains supervisor consultation requirements")
            else:
                print("   ❌ Missing supervisor consultation requirements")
                return False
                
            # Should NOT contain multi-agent specific content
            if 'send_message' not in prompt and 'NEVER WORK IN ISOLATION' not in prompt:
                print("   ✅ Does not contain multi-agent specific content")
            else:
                print("   ❌ Contains multi-agent specific content")
                return False
        else:
            print("   ❌ Single-agent prompt not loaded")
            return False
            
    except Exception as e:
        print(f"   ❌ Error loading SingleAgentMode: {e}")
        return False
    
    # Test 4: Test MultiAgentMode loads unified prompts
    print("\n4. Testing MultiAgentMode with unified prompts...")
    try:
        multi_mode = MultiAgentMode(
            num_agents=3,
            agent_model="test_model",
            orchestrator_model="test_model",
            audit_model="test_model", 
            max_cost_per_agent=None,
            max_iterations_per_agent=None,
            run_parallel=True,
            auto_commit=False
        )
        
        prompts = multi_mode.system_prompts
        if 'multi_agent_prompt' in prompts:
            prompt = prompts['multi_agent_prompt']
            print(f"   ✅ Multi-agent prompt loaded: {len(prompt)} chars")
            
            # Check for key elements
            if 'MULTI-AGENT MISSION' in prompt:
                print("   ✅ Contains multi-agent mission statement")
            else:
                print("   ❌ Missing multi-agent mission statement")
                return False
                
            if 'send_message' in prompt and 'ask_supervisor' in prompt:
                print("   ✅ Contains team communication requirements")
            else:
                print("   ❌ Missing team communication requirements")
                return False
                
            if 'NEVER WORK IN ISOLATION' in prompt:
                print("   ✅ Contains isolation prevention rules")
            else:
                print("   ❌ Missing isolation prevention rules")
                return False
        else:
            print("   ❌ Multi-agent prompt not loaded")
            return False
            
    except Exception as e:
        print(f"   ❌ Error loading MultiAgentMode: {e}")
        return False
    
    # Test 5: Test prompt formatting works
    print("\n5. Testing prompt formatting...")
    
    # Test single-agent formatting
    single_prompt = single_mode.system_prompts['single_agent_prompt']
    try:
        formatted_single = single_prompt.format(
            agent_id="test_agent",
            model="test_model",
            group_description="Test task group",
            group_id="test_group_1", 
            specialization="backend_dev",
            available_tools="create_file, read_file, api_test",
            mandatory_context_json="{{context}}",
            task_description="{{task}}"
        )
        
        if "test_agent" in formatted_single and "Test task group" in formatted_single:
            print("   ✅ Single-agent prompt formatting works")
        else:
            print("   ❌ Single-agent prompt formatting failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Single-agent prompt formatting error: {e}")
        return False
    
    # Test multi-agent formatting
    multi_prompt = multi_mode.system_prompts['multi_agent_prompt']
    try:
        formatted_multi = multi_prompt.format(
            agent_id="qa_agent_test",
            model="test_model",
            group_description="Test multi-agent task",
            group_id="test_group_2",
            specialization="qa_engineer",
            available_tools="run_tests, test_coverage, lint_code",
            mandatory_context_json="{{context}}",
            task_description="{{task}}"
        )
        
        if "qa_agent_test" in formatted_multi and "Test multi-agent task" in formatted_multi:
            print("   ✅ Multi-agent prompt formatting works")
        else:
            print("   ❌ Multi-agent prompt formatting failed")
            print(f"      Debug: 'qa_agent_test' in result: {'qa_agent_test' in formatted_multi}")
            print(f"      Debug: 'Test multi-agent task' in result: {'Test multi-agent task' in formatted_multi}")
            return False
            
    except Exception as e:
        print(f"   ❌ Multi-agent prompt formatting error: {e}")
        return False
    
    # Test 6: Check configuration completeness
    print("\n6. Testing configuration completeness...")
    
    config_dir = Path('equitrcoder/config')
    expected_config_files = {
        'default.yaml',           # App configuration
        'profiles.yaml',          # Profile system & default tools
        'system_prompt.yaml',     # Unified system prompts (includes orchestrator prompts)
    }
    
    actual_config_files = {f.name for f in config_dir.glob('*.yaml')}
    
    if expected_config_files.issubset(actual_config_files):
        print(f"   ✅ All {len(expected_config_files)} config files present")
    else:
        missing = expected_config_files - actual_config_files
        extra = actual_config_files - expected_config_files
        if missing:
            print(f"   ❌ Missing config files: {missing}")
        if extra:
            print(f"   ℹ️  Extra config files: {extra}")
        if missing:
            return False
    
    # Test 7: Verify prompt completeness
    print("\n7. Testing prompt completeness...")
    
    # Check that both prompts are complete and distinct
    single_prompt = system_config['single_agent_prompt']
    multi_prompt = system_config['multi_agent_prompt']
    
    # Both should have core elements
    core_elements = ['CRITICAL RULES', 'MANDATORY TOOL USE', 'TODO COMPLETION', 'AVAILABLE TOOLS']
    
    single_has_core = all(element in single_prompt for element in core_elements)
    multi_has_core = all(element in multi_prompt for element in core_elements)
    
    if single_has_core and multi_has_core:
        print("   ✅ Both prompts contain core elements")
    else:
        print(f"   ❌ Missing core elements - Single: {single_has_core}, Multi: {multi_has_core}")
        return False
    
    # Check distinctiveness
    single_specific = ['SINGLE-AGENT MISSION', 'SUPERVISOR CONSULTATION']
    multi_specific = ['MULTI-AGENT MISSION', 'TEAM COMMUNICATION', 'NEVER WORK IN ISOLATION']
    
    single_has_specific = all(element in single_prompt for element in single_specific)
    multi_has_specific = all(element in multi_prompt for element in multi_specific)
    
    if single_has_specific and multi_has_specific:
        print("   ✅ Both prompts have mode-specific content")
    else:
        print(f"   ❌ Missing mode-specific content - Single: {single_has_specific}, Multi: {multi_has_specific}")
        return False
    
    # Check separation (single shouldn't have multi content and vice versa)
    single_has_multi_content = any(element in single_prompt for element in multi_specific)
    multi_has_single_only_content = 'SINGLE-AGENT MISSION' in multi_prompt
    
    if not single_has_multi_content and not multi_has_single_only_content:
        print("   ✅ Prompts are properly separated")
    else:
        print(f"   ❌ Prompts have cross-contamination")
        return False
    
    print("\n🎉 All unified prompt tests passed!")
    print("\n📋 Unified Prompt System Summary:")
    print(f"   - Configuration files: {len(expected_config_files)}")
    print(f"   - System prompts: 2 (unified single-agent, unified multi-agent)")
    print(f"   - Prompt separation: ✅ Clean")
    print(f"   - Prompt formatting: ✅ Working")
    print(f"   - Mode-specific content: ✅ Properly separated")
    print(f"   - Fragmentation eliminated: ✅ Single source of truth")
    
    return True

if __name__ == "__main__":
    success = test_unified_prompts()
    print(f"\n{'🎉 Unified prompt system working correctly!' if success else '❌ Unified prompt system has issues!'}")