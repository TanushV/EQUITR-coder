import asyncio
from testing.comprehensive_test_framework import ComprehensiveTestController

async def main():
    """Run only the multi-agent parallel tests."""
    controller = ComprehensiveTestController()
    print("⚡ MULTI-AGENT PARALLEL TESTING")
    await controller.run_multi_agent_parallel_tests()

if __name__ == "__main__":
    asyncio.run(main()) 