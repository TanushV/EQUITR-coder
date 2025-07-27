#!/usr/bin/env python3
"""Test the new mandatory 3-document workflow."""

import asyncio
import sys
import os

# Add parent directory to path so we can import equitrcoder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from equitrcoder.programmatic.interface import EquitrCoder, TaskConfiguration

async def test_programmatic_workflow():
    print('🧪 Testing programmatic interface with mandatory 3-document workflow...')
    
    # Create single-agent coder
    coder = EquitrCoder(mode='single', repo_path='.')
    
    # Test task configuration
    config = TaskConfiguration(
        description='Create a simple calculator',
        model='moonshot/kimi-k2-0711-preview',
        max_cost=0.05,
        max_iterations=3
    )
    
    # Execute task with mandatory document creation
    result = await coder.execute_task('Create a simple calculator', config)
    
    print(f'Result: {result.success}')
    if result.error:
        print(f'Error: {result.error}')
    
    print(f'Cost: ${result.cost:.4f}')
    print(f'Iterations: {result.iterations}')

if __name__ == "__main__":
    asyncio.run(test_programmatic_workflow())