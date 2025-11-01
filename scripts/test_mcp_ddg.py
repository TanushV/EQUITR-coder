import asyncio
import json


async def main():
    # Defer imports so the script runs even if optional deps are missing
    try:
        from equitrcoder.tools.discovery import discover_tools
    except Exception as e:
        print(
            json.dumps({"success": False, "error": f"Failed to import discovery: {e}"})
        )
        return

    try:
        tools = discover_tools()
        ddg = next((t for t in tools if t.get_name() == "mcp:ddg-search"), None)
        if not ddg:
            print(
                json.dumps({"success": False, "error": "Tool mcp:ddg-search not found"})
            )
            return
        res = await ddg.run(
            tool="search",
            arguments={"query": "site:python.org asyncio", "max_results": 3},
        )
        print(
            json.dumps({"success": res.success, "data": res.data, "error": res.error})
        )
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))


if __name__ == "__main__":
    asyncio.run(main())
