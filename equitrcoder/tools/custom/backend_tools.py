"""
Backend development tools for API testing, database operations, and server management.
"""

import subprocess
import requests
from typing import Type, Dict, Any, Optional
from pydantic import BaseModel, Field

from ..base import Tool, ToolResult


class ApiTestArgs(BaseModel):
    url: str = Field(..., description="API endpoint URL to test")
    method: str = Field(
        default="GET", description="HTTP method (GET, POST, PUT, DELETE, etc.)"
    )
    headers: Dict[str, str] = Field(
        default_factory=dict, description="HTTP headers to send"
    )
    data: Optional[Dict[str, Any]] = Field(
        default=None, description="Request body data (for POST/PUT)"
    )
    timeout: int = Field(default=30, description="Request timeout in seconds")


class ApiTest(Tool):
    def get_name(self) -> str:
        return "api_test"

    def get_description(self) -> str:
        return "Test API endpoints with various HTTP methods and validate responses"

    def get_args_schema(self) -> Type[BaseModel]:
        return ApiTestArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)
            headers = self._prepare_headers(args)
            response = self._make_request(args, headers)
            response_data = self._parse_response(response)

            return self._create_result(response, response_data, args)

        except requests.exceptions.Timeout:
            return ToolResult(
                success=False, error=f"Request timed out after {args.timeout} seconds"
            )
        except requests.exceptions.ConnectionError:
            return ToolResult(success=False, error=f"Failed to connect to {args.url}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def _prepare_headers(self, args) -> dict:
        """Prepare request headers with defaults"""
        headers = args.headers or {}
        if "Content-Type" not in headers and args.data:
            headers["Content-Type"] = "application/json"
        return headers

    def _make_request(self, args, headers):
        """Make the HTTP request"""
        return requests.request(
            method=args.method.upper(),
            url=args.url,
            headers=headers,
            json=args.data if args.data else None,
            timeout=args.timeout,
        )

    def _parse_response(self, response):
        """Parse response data, falling back to text if JSON parsing fails"""
        try:
            return response.json()
        except (ValueError, TypeError, AttributeError):
            return response.text

    def _create_result(self, response, response_data, args):
        """Create the final ToolResult"""
        is_success = 200 <= response.status_code < 400
        error_msg = (
            f"HTTP {response.status_code}: {response.reason}"
            if response.status_code >= 400
            else None
        )

        return ToolResult(
            success=is_success,
            data={
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "response_data": response_data,
                "response_time": response.elapsed.total_seconds(),
                "url": args.url,
                "method": args.method.upper(),
            },
            error=error_msg,
        )


class DatabaseQueryArgs(BaseModel):
    query: str = Field(..., description="SQL query to execute")
    database_url: str = Field(
        default="sqlite:///./test.db", description="Database connection URL"
    )
    fetch_results: bool = Field(
        default=True, description="Whether to fetch and return query results"
    )


class DatabaseQuery(Tool):
    def get_name(self) -> str:
        return "database_query"

    def get_description(self) -> str:
        return "Execute SQL queries against a database (supports SQLite by default)"

    def get_args_schema(self) -> Type[BaseModel]:
        return DatabaseQueryArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)

            # For now, implement SQLite support (can be extended for other databases)
            if args.database_url.startswith("sqlite:"):
                return await self._execute_sqlite_query(args)
            else:
                return ToolResult(
                    success=False,
                    error="Only SQLite databases are currently supported. Use sqlite:///path/to/db.db format.",
                )

        except Exception as e:
            return ToolResult(success=False, error=str(e))

    async def _execute_sqlite_query(self, args: DatabaseQueryArgs) -> ToolResult:
        try:
            import sqlite3

            db_path = self._extract_db_path(args.database_url)
            conn = self._create_connection(db_path)
            cursor = conn.cursor()
            cursor.execute(args.query)

            if self._is_select_query(args.query):
                return self._handle_select_query(cursor, args, db_path)
            else:
                return self._handle_modify_query(conn, cursor, args, db_path)

        except sqlite3.Error as e:
            return ToolResult(success=False, error=f"SQLite error: {str(e)}")
        except ImportError:
            return ToolResult(success=False, error="sqlite3 module not available")
        finally:
            if "conn" in locals():
                conn.close()

    def _extract_db_path(self, database_url: str) -> str:
        """Extract database path from URL"""
        return database_url.replace("sqlite:///", "").replace("sqlite://", "")

    def _create_connection(self, db_path: str):
        """Create SQLite connection with row factory"""
        import sqlite3

        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _is_select_query(self, query: str) -> bool:
        """Check if query is a SELECT or PRAGMA query"""
        return query.strip().upper().startswith(("SELECT", "PRAGMA"))

    def _handle_select_query(
        self, cursor, args: DatabaseQueryArgs, db_path: str
    ) -> ToolResult:
        """Handle SELECT queries that return results"""
        if args.fetch_results:
            results = [dict(row) for row in cursor.fetchall()]
            return ToolResult(
                success=True,
                data={
                    "results": results,
                    "row_count": len(results),
                    "query": args.query,
                    "database": db_path,
                },
            )
        else:
            return ToolResult(
                success=True,
                data={
                    "message": "Query executed successfully (results not fetched)",
                    "query": args.query,
                    "database": db_path,
                },
            )

    def _handle_modify_query(
        self, conn, cursor, args: DatabaseQueryArgs, db_path: str
    ) -> ToolResult:
        """Handle INSERT/UPDATE/DELETE queries"""
        conn.commit()
        affected_rows = cursor.rowcount

        return ToolResult(
            success=True,
            data={
                "affected_rows": affected_rows,
                "query": args.query,
                "database": db_path,
                "message": f"Query executed successfully, {affected_rows} rows affected",
            },
        )


class StartServerArgs(BaseModel):
    command: str = Field(
        ...,
        description="Command to start the server (e.g., 'python app.py', 'uvicorn main:app')",
    )
    port: int = Field(default=8000, description="Port to run the server on")
    host: str = Field(default="127.0.0.1", description="Host to bind the server to")
    background: bool = Field(default=True, description="Run server in background")


class StartServer(Tool):
    def get_name(self) -> str:
        return "start_server"

    def get_description(self) -> str:
        return "Start a development server for testing APIs and web applications"

    def get_args_schema(self) -> Type[BaseModel]:
        return StartServerArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)

            # Modify command to include host and port if not already specified
            cmd_parts = args.command.split()

            # Add host and port for common server commands
            if any(
                server_cmd in cmd_parts[0]
                for server_cmd in ["uvicorn", "gunicorn", "flask"]
            ):
                if "--host" not in args.command:
                    cmd_parts.extend(["--host", args.host])
                if "--port" not in args.command:
                    cmd_parts.extend(["--port", str(args.port)])

            if args.background:
                # Start server in background
                process = subprocess.Popen(
                    cmd_parts, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
                )

                # Give it a moment to start
                import time

                time.sleep(2)

                # Check if process is still running
                if process.poll() is None:
                    return ToolResult(
                        success=True,
                        data={
                            "message": f"Server started successfully on {args.host}:{args.port}",
                            "pid": process.pid,
                            "command": " ".join(cmd_parts),
                            "url": f"http://{args.host}:{args.port}",
                            "background": True,
                        },
                    )
                else:
                    stdout, stderr = process.communicate()
                    return ToolResult(
                        success=False,
                        error=f"Server failed to start: {stderr}",
                        data={"stdout": stdout, "stderr": stderr},
                    )
            else:
                # Run server in foreground (for testing)
                result = subprocess.run(
                    cmd_parts,
                    capture_output=True,
                    text=True,
                    timeout=10,  # Short timeout for foreground testing
                )

                return ToolResult(
                    success=result.returncode == 0,
                    data={
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "return_code": result.returncode,
                        "command": " ".join(cmd_parts),
                    },
                    error=result.stderr if result.returncode != 0 else None,
                )

        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error="Server command timed out")
        except Exception as e:
            return ToolResult(success=False, error=str(e))
