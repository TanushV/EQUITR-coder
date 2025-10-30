## MCP Integration Guide

This project supports connecting to external Model Context Protocol (MCP) servers and exposing their tools to agents via dynamic proxy tools. See MCP SDK references (Context7) for stdio client usage and patterns.

### What you get
- Automatic discovery of MCP servers declared in a JSON config
- A generic tool per server (named `mcp:<serverName>`) that lets agents call any tool exposed by that server
- Stdio transport support out-of-the-box using the official MCP Python SDK

### Requirements
- Python MCP SDK (optional install):

```bash
pip install modelcontextprotocol
```

If you don't install it, MCP tools will be skipped at runtime.

### Configuration
EQUITR Coder looks for an MCP servers JSON config in the following locations (first found wins):
1. Environment variable `EQUITR_MCP_SERVERS` pointing to a JSON file
2. `~/.EQUITR-coder/mcp_servers.json`
3. Packaged default: `equitrcoder/config/mcp_servers.json`

JSON structure (inspired by the MCP Python SDK examples):

```json
{
  "mcpServers": {
    "sqlite": {
      "command": "uvx",
      "args": ["mcp-server-sqlite", "--db-path", "./test.db"],
      "env": {},
      "transport": "stdio"
    },
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
      "env": {},
      "transport": "stdio"
    }
  }
}
```

Fields:
- `command`: Executable to launch the server (e.g., `uvx`, `npx`, `python`)
- `args`: Arguments for the process
- `env`: Extra environment variables
- `transport`: Currently only `stdio` is supported

### How tools appear
For each configured server, a dynamic tool is registered named `mcp:<serverName>`. It accepts:

```json
{
  "tool": "<remoteToolName>",
  "arguments": { "key": "value" }
}
```

On call, we connect to the server (stdio), initialize a client session, invoke the remote tool, and return structured results if available.

### Example: call a remote fetch tool
In multi-agent modes the tool is available automatically after startup. For programmatic usage, discover tools via the API endpoints or introspect the registry.

### Using Context7 documentation
We rely on authoritative MCP references. Helpful starting points:
- Python SDK: Context7 entry `/modelcontextprotocol/python-sdk` — clients/servers, stdio and SSE transports, and configuration patterns.
- Specification and guides: `/websites/modelcontextprotocol_io_specification` and related entries.

Key snippets align with the SDK docs, e.g., defining `StdioServerParameters` and connecting with `stdio_client`, as in the Python SDK examples.

### Troubleshooting
- No `mcp:*` tools appear: ensure `modelcontextprotocol` is installed and the JSON config is found/valid.
- Server fails to launch: verify `command`/`args` work in your shell.
- Long-running server calls: each invocation performs a connect-call-disconnect cycle to keep things robust; if you need persistent sessions, extend `runtime_client.py` to cache sessions.

---

## DuckDuckGo MCP server (no API keys)

This project includes a ready-to-use config entry for the DuckDuckGo MCP server (`ddg-search`). It provides `search` and `fetch_content` tools and requires no API keys.

### 1) Install prerequisites

- Install uv (choose one):

```bash
brew install uv                  # macOS
winget install astral-sh.uv -e   # Windows
```

### 2) Install the server

```bash
uv pip install duckduckgo-mcp-server
```

### 3) Verify with MCP Inspector (optional)

```bash
# Opens Inspector at http://localhost:6274
npx @modelcontextprotocol/inspector -- uvx duckduckgo-mcp-server
```

You should see two tools: `search(query, max_results?)` and `fetch_content(url)`.

### 4) Configure the client (this project)

You can copy from the included registry entry instead of using a hardcoded default.

Suggested `~/.EQUITR-coder/mcp_servers.json` for DuckDuckGo:

```json
{
  "mcpServers": {
    "ddg-search": {
      "command": "uvx",
      "args": ["duckduckgo-mcp-server"],
      "env": {},
      "transport": "stdio"
    }
  }
}
```

We do not ship hardcoded MCP servers in the default; use the above user config or consult `equitrcoder/config/mcp_registry.json` for copy-paste entries.

### 5) Test end-to-end

- Ensure the MCP Python SDK is installed:

```bash
pip install "equitrcoder[mcp]"
```

- List tools in this project:

```bash
equitrcoder tools --list
```

Look for `mcp:ddg-search`.

- Run the provided test script:

```bash
python scripts/test_mcp_ddg.py
```

Expected: JSON output with `success: true` and either `structuredContent` or `content` containing search results.


