"""
FastAPI server for equitrcoder.
"""

from typing import Any, Dict, List, Optional

try:
    import uvicorn
    from fastapi import FastAPI as _FastAPI, HTTPException as _HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    HAS_FASTAPI = True
except Exception:  # pragma: no cover - import guard for mypy
    HAS_FASTAPI = False

from pydantic import BaseModel

from ..agents.base_agent import BaseAgent
# Import orchestrators lazily inside functions to avoid mypy errors when optional
# modules are not present in minimal environments.
from ..tools.discovery import discover_tools


class TaskRequest(BaseModel):
    task_description: str
    max_cost: Optional[float] = None
    max_iterations: Optional[int] = None
    session_id: Optional[str] = None


class WorkerRequest(BaseModel):
    worker_id: str
    scope_paths: List[str]
    allowed_tools: List[str]
    max_cost: Optional[float] = None
    max_iterations: Optional[int] = None


class MultiTaskRequest(BaseModel):
    coordination_task: str
    workers: List[WorkerRequest]
    max_cost: Optional[float] = 10.0


def create_app() -> Any:
    """Create FastAPI application."""
    if not HAS_FASTAPI:
        raise ImportError(
            "FastAPI not available. Install with: pip install equitrcoder[api]"
        )

    app = _FastAPI(
        title="EQUITR Coder API",
        description="API for the EQUITR Coder multi-agent system",
        version="1.0.0",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global state
    orchestrators: Dict[str, Any] = {}

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "EQUITR Coder API",
            "version": "1.0.0",
            "endpoints": [
                "/single/execute",
                "/multi/create",
                "/multi/{orchestrator_id}/execute",
                "/tools",
                "/health",
            ],
        }

    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "healthy", "active_orchestrators": len(orchestrators)}

    @app.get("/tools")
    async def get_tools():
        """Get available tools."""
        tools = discover_tools()
        return {
            "tools": [
                {
                    "name": tool.get_name(),
                    "description": tool.get_description(),
                    "schema": tool.get_json_schema(),
                }
                for tool in tools
            ]
        }

    @app.post("/single/execute")
    async def execute_single_task(request: TaskRequest):
        """Execute a single-agent task."""
        try:
            # Create agent
            agent = BaseAgent(
                max_cost=request.max_cost, max_iterations=request.max_iterations
            )

            # Add tools
            tools = discover_tools()
            for tool in tools:
                agent.add_tool(tool)

            # Import orchestrator lazily
            from ..orchestrators.single_orchestrator import SingleAgentOrchestrator  # type: ignore[import-not-found]

            # Create orchestrator
            orchestrator = SingleAgentOrchestrator(
                agent=agent,
                max_cost=request.max_cost,
                max_iterations=request.max_iterations,
            )

            # Execute task
            result = await orchestrator.execute_task(
                task_description=request.task_description, session_id=request.session_id
            )

            return result

        except Exception as e:  # pragma: no cover - runtime error mapping
            raise _HTTPException(status_code=500, detail=str(e))

    @app.post("/multi/create")
    async def create_multi_orchestrator(workers: List[WorkerRequest]):
        """Create a multi-agent orchestrator."""
        try:
            orchestrator_id = f"orchestrator_{len(orchestrators)}"

            from ..orchestrators.multi_agent_orchestrator import (  # type: ignore[import-not-found]
                MultiAgentOrchestrator,
                WorkerConfig,
            )

            orchestrator = MultiAgentOrchestrator(
                max_concurrent_workers=len(workers),
                global_cost_limit=sum(w.max_cost or 1.0 for w in workers),
            )

            # Create workers
            for worker_req in workers:
                config = WorkerConfig(
                    worker_id=worker_req.worker_id,
                    scope_paths=worker_req.scope_paths,
                    allowed_tools=worker_req.allowed_tools,
                    max_cost=worker_req.max_cost,
                    max_iterations=worker_req.max_iterations,
                )
                orchestrator.create_worker(config)

            orchestrators[orchestrator_id] = orchestrator

            return {
                "orchestrator_id": orchestrator_id,
                "status": "created",
                "workers": len(workers),
            }

        except Exception as e:  # pragma: no cover - runtime error mapping
            raise _HTTPException(status_code=500, detail=str(e))

    @app.post("/multi/{orchestrator_id}/execute")
    async def execute_multi_task(orchestrator_id: str, request: MultiTaskRequest):
        """Execute a multi-agent coordination task."""
        if orchestrator_id not in orchestrators:
            raise _HTTPException(status_code=404, detail="Orchestrator not found")

        try:
            orchestrator = orchestrators[orchestrator_id]

            # Create worker tasks
            worker_tasks: List[Dict[str, Any]] = []
            for i, worker_req in enumerate(request.workers):
                worker_tasks.append(
                    {
                        "task_id": f"task_{i}",
                        "worker_id": worker_req.worker_id,
                        "task_description": f"Part {i+1} of: {request.coordination_task}",
                        "context": {"part": i + 1, "total_parts": len(request.workers)},
                    }
                )

            # Execute coordination
            result = await orchestrator.coordinate_workers(
                coordination_task=request.coordination_task, worker_tasks=worker_tasks
            )

            return result

        except Exception as e:  # pragma: no cover - runtime error mapping
            raise _HTTPException(status_code=500, detail=str(e))

    @app.get("/multi/{orchestrator_id}/status")
    async def get_orchestrator_status(orchestrator_id: str):
        """Get orchestrator status."""
        if orchestrator_id not in orchestrators:
            raise _HTTPException(status_code=404, detail="Orchestrator not found")

        orchestrator = orchestrators[orchestrator_id]
        return orchestrator.get_orchestrator_status()

    @app.delete("/multi/{orchestrator_id}")
    async def delete_orchestrator(orchestrator_id: str):
        """Delete an orchestrator."""
        if orchestrator_id not in orchestrators:
            raise _HTTPException(status_code=404, detail="Orchestrator not found")

        orchestrator = orchestrators[orchestrator_id]
        await orchestrator.shutdown()
        del orchestrators[orchestrator_id]

        return {"message": "Orchestrator deleted"}

    return app


def start_server(host: str = "localhost", port: int = 8000):
    """Start the API server."""
    if not HAS_FASTAPI:
        raise ImportError(
            "FastAPI not available. Install with: pip install equitrcoder[api]"
        )

    app = create_app()

    try:
        uvicorn.run(app, host=host, port=port)
    except KeyboardInterrupt:  # pragma: no cover - CLI convenience
        print("\n Server stopped")
