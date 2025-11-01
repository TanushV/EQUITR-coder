"""
FastAPI server for equitrcoder.
"""

from typing import Any, Dict, List, Optional

try:
    import uvicorn
    from fastapi import FastAPI as _FastAPI
    from fastapi import HTTPException as _HTTPException
    from fastapi.middleware.cors import CORSMiddleware

    HAS_FASTAPI = True
except Exception:  # pragma: no cover - import guard for mypy
    HAS_FASTAPI = False

from pydantic import BaseModel

from ..modes.multi_agent_mode import run_multi_agent_parallel
from ..modes.single_agent_mode import run_single_agent_mode

# Import orchestrators lazily inside functions to avoid mypy errors when optional
# modules are not present in minimal environments.
from ..tools.discovery import discover_tools


class TaskRequest(BaseModel):
    task_description: str
    max_cost: Optional[float] = None
    max_iterations: Optional[int] = None
    session_id: Optional[str] = None
    model: Optional[str] = None


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
    supervisor_model: Optional[str] = None
    worker_model: Optional[str] = None


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
        """Execute a single-agent task via clean architecture."""
        try:
            # Simple path: call run_single_agent_mode directly
            model = request.model or "moonshot/kimi-k2-0711-preview"
            result = await run_single_agent_mode(
                task_description=request.task_description,
                agent_model=model,
                orchestrator_model=model,
                audit_model=model,
                max_cost=request.max_cost,
                max_iterations=request.max_iterations,
                project_path=".",
            )
            return result
        except Exception as e:  # pragma: no cover - runtime error mapping
            raise _HTTPException(status_code=500, detail=str(e))

    @app.post("/multi/create")
    async def create_multi_orchestrator(workers: List[WorkerRequest]):
        """Create a multi-agent orchestrator (lightweight registry)."""
        try:
            orchestrator_id = f"orchestrator_{len(orchestrators)}"
            # Minimal stub to track workers in-memory
            orchestrators[orchestrator_id] = {
                "workers": [w.model_dump() for w in workers]
            }
            return {
                "orchestrator_id": orchestrator_id,
                "status": "created",
                "workers": len(workers),
            }
        except Exception as e:  # pragma: no cover - runtime error mapping
            raise _HTTPException(status_code=500, detail=str(e))

    @app.post("/multi/{orchestrator_id}/execute")
    async def execute_multi_task(orchestrator_id: str, request: MultiTaskRequest):
        """Execute a multi-agent coordination task via clean architecture."""
        if orchestrator_id not in orchestrators:
            raise _HTTPException(status_code=404, detail="Orchestrator not found")

        try:
            team = None  # team selection can be added later
            supervisor_model = (
                request.supervisor_model or "moonshot/kimi-k2-0711-preview"
            )
            worker_model = request.worker_model or "moonshot/kimi-k2-0711-preview"
            result = await run_multi_agent_parallel(
                task_description=request.coordination_task,
                num_agents=len(request.workers) if request.workers else 2,
                agent_model=worker_model,
                orchestrator_model=supervisor_model,
                audit_model=supervisor_model,
                max_cost_per_agent=(request.max_cost or 10.0)
                / max(1, len(request.workers) or 1),
                max_iterations_per_agent=50,
                auto_commit=True,
                team=team,
            )
            return result
        except Exception as e:  # pragma: no cover - runtime error mapping
            raise _HTTPException(status_code=500, detail=str(e))

    @app.get("/multi/{orchestrator_id}/status")
    async def get_orchestrator_status(orchestrator_id: str):
        """Get orchestrator status (stub)."""
        if orchestrator_id not in orchestrators:
            raise _HTTPException(status_code=404, detail="Orchestrator not found")

        return {
            "orchestrator_id": orchestrator_id,
            "workers": len(orchestrators[orchestrator_id]["workers"]),
        }

    @app.delete("/multi/{orchestrator_id}")
    async def delete_orchestrator(orchestrator_id: str):
        """Delete an orchestrator."""
        if orchestrator_id not in orchestrators:
            raise _HTTPException(status_code=404, detail="Orchestrator not found")

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
