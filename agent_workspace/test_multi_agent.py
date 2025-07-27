#!/usr/bin/env python3
"""Test the multi-agent workflow with split todos."""

import asyncio
import sys
import os

# Add parent directory to path so we can import equitrcoder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from equitrcoder.programmatic.interface import EquitrCoder, MultiAgentTaskConfiguration

async def test_multi_agent_workflow():
    print('🧪 Testing multi-agent interface with split todos...')
    
    # Create multi-agent coder
    coder = EquitrCoder(mode='multi', repo_path='.')
    
    # Test task configuration
    config = MultiAgentTaskConfiguration(
        description='Create a simple web server',
        max_workers=2,
        supervisor_model='moonshot/kimi-k2-0711-preview',
        worker_model='moonshot/kimi-k2-0711-preview',
        max_cost=0.10
    )
    
    # Execute task with mandatory document creation and split todos
    result = await coder.execute_task('Create a simple web server', config)
    
    print(f'Result: {result.success}')
    if result.error:
        print(f'Error: {result.error}')
    
    print(f'Cost: ${result.cost:.4f}')
    print(f'Iterations: {result.iterations}')

if __name__ == "__main__":
    asyncio.run(test_multi_agent_workflow())