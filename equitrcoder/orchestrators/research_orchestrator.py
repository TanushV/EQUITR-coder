"""
Research Orchestrator for iterative ML/research workflows.

This module extends MultiAgentOrchestrator to provide specialized functionality for
machine learning research, including machine-aware scaling, dataset handling,
and iterative experimentation workflows.
"""

import json
import os
import time
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable

try:
    import psutil
    import torch

    _TORCH_AVAILABLE = True
except ImportError:
    torch = None
    _TORCH_AVAILABLE = False

from .multi_agent_orchestrator import MultiAgentOrchestrator, WorkerConfig
from ..core.session import SessionManagerV2
from ..providers.openrouter import OpenRouterProvider


@dataclass
class MachineSpecs:
    """Machine specifications for scaling experiments."""

    os_type: str
    cpu_cores: int
    cpu_physical_cores: int
    ram_gb: float
    gpu_available: bool = False
    gpu_count: int = 0
    gpu_memory_gb: float = 0.0


@dataclass
class ExperimentConfig:
    """Configuration for a research experiment."""

    experiment_id: str
    name: str
    description: str
    dataset_path: Optional[str] = None
    hyperparameters: Dict[str, Any] = None
    environment_requirements: List[str] = None
    expected_duration_mins: Optional[int] = None
    scale_factor: float = 1.0


@dataclass
class ExperimentResult:
    """Result of a research experiment."""

    experiment_id: str
    success: bool
    metrics: Dict[str, Any] = None
    logs: List[str] = None
    artifacts: List[str] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    scaled_params: Dict[str, Any] = None


class ResearchOrchestrator(MultiAgentOrchestrator):
    """
    Specialized orchestrator for ML research workflows with machine-aware scaling
    and iterative experimentation capabilities.
    """

    def __init__(
        self,
        supervisor_provider: Optional[OpenRouterProvider] = None,
        worker_provider: Optional[OpenRouterProvider] = None,
        session_manager: Optional[SessionManagerV2] = None,
        repo_path: str = ".",
        max_concurrent_workers: int = 3,
        global_cost_limit: float = 10.0,
        max_total_iterations: int = 100,
        context_max_tokens: int = 8000,
        scale_factor: float = 1.0,
        experiments_dir: str = "./experiments",
        sandbox_limits: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            supervisor_provider=supervisor_provider,
            worker_provider=worker_provider,
            session_manager=session_manager,
            repo_path=repo_path,
            max_concurrent_workers=max_concurrent_workers,
            global_cost_limit=global_cost_limit,
            max_total_iterations=max_total_iterations,
            context_max_tokens=context_max_tokens,
        )

        self.scale_factor = scale_factor
        self.experiments_dir = Path(experiments_dir)
        self.experiments_dir.mkdir(parents=True, exist_ok=True)

        # Sandbox limits for safe execution
        self.sandbox_limits = sandbox_limits or {
            "max_memory_mb": 2048,
            "timeout_seconds": 300,
            "max_processes": 4,
        }

        # Research state
        self.machine_specs: Optional[MachineSpecs] = None
        self.current_experiment: Optional[ExperimentConfig] = None
        self.experiment_history: List[ExperimentResult] = []

        # Research-specific callbacks
        self.on_experiment_start_callback: Optional[Callable] = None
        self.on_experiment_complete_callback: Optional[Callable] = None
        self.on_machine_detected_callback: Optional[Callable] = None

    def _detect_machine_specs(self) -> MachineSpecs:
        """Detect machine specifications for scaling experiments."""
        try:
            # CPU information
            cpu_cores = psutil.cpu_count(logical=True)
            cpu_physical_cores = psutil.cpu_count(logical=False)

            # Memory information
            memory = psutil.virtual_memory()
            ram_gb = memory.total / (1024**3)

            # OS information
            os_type = os.name

            # GPU information
            gpu_available = False
            gpu_count = 0
            gpu_memory_gb = 0.0

            if _TORCH_AVAILABLE and torch.cuda.is_available():
                gpu_available = True
                gpu_count = torch.cuda.device_count()
                if gpu_count > 0:
                    # Get memory of first GPU as representative
                    gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (
                        1024**3
                    )

            specs = MachineSpecs(
                os_type=os_type,
                cpu_cores=cpu_cores,
                cpu_physical_cores=cpu_physical_cores,
                ram_gb=ram_gb,
                gpu_available=gpu_available,
                gpu_count=gpu_count,
                gpu_memory_gb=gpu_memory_gb,
            )

            self.machine_specs = specs

            if self.on_machine_detected_callback:
                self.on_machine_detected_callback(specs)

            return specs

        except Exception:
            # Fallback to conservative defaults
            specs = MachineSpecs(
                os_type="unknown",
                cpu_cores=2,
                cpu_physical_cores=2,
                ram_gb=4.0,
                gpu_available=False,
            )
            self.machine_specs = specs
            return specs

    def _scale_experiment_params(
        self, base_params: Dict[str, Any], machine_specs: MachineSpecs
    ) -> Dict[str, Any]:
        """Scale experiment parameters based on machine specifications."""
        scaled_params = base_params.copy()

        # Apply global scale factor
        scale_factor = self.scale_factor

        # Adjust based on available resources
        if machine_specs.ram_gb < 8:
            scale_factor *= 0.5  # Reduce for low memory systems
        elif machine_specs.ram_gb > 16:
            scale_factor *= 1.5  # Increase for high memory systems

        if machine_specs.cpu_cores < 4:
            scale_factor *= 0.7  # Reduce for low CPU systems
        elif machine_specs.cpu_cores > 8:
            scale_factor *= 1.2  # Increase for high CPU systems

        # Scale common ML parameters
        if "batch_size" in scaled_params:
            original_batch_size = scaled_params["batch_size"]
            scaled_params["batch_size"] = max(
                1, int(original_batch_size * scale_factor)
            )

        if "num_workers" in scaled_params:
            max_workers = min(machine_specs.cpu_cores - 1, 8)  # Leave one core free
            scaled_params["num_workers"] = min(
                scaled_params["num_workers"], max_workers
            )

        if "epochs" in scaled_params and scale_factor < 1.0:
            # Reduce epochs for resource-constrained systems
            original_epochs = scaled_params["epochs"]
            scaled_params["epochs"] = max(1, int(original_epochs * scale_factor))

        # GPU-specific scaling
        if machine_specs.gpu_available:
            if "device" not in scaled_params:
                scaled_params["device"] = "cuda"
            if "precision" not in scaled_params and machine_specs.gpu_memory_gb < 8:
                scaled_params["precision"] = "fp16"  # Use half precision for low VRAM
        else:
            scaled_params["device"] = "cpu"

        return scaled_params

    async def _prompt_for_dataset(self, experiment_name: str) -> Optional[str]:
        """Prompt user for dataset path and validate it."""
        # In a real implementation, this would use the supervisor or a UI component
        # For now, we'll check common dataset locations

        common_paths = [
            f"./data/{experiment_name.lower()}",
            f"./datasets/{experiment_name.lower()}",
            "./data",
            "./datasets",
        ]

        for path in common_paths:
            dataset_path = Path(path)
            if dataset_path.exists() and (
                any(dataset_path.glob("*.csv"))
                or any(dataset_path.glob("*.json"))
                or any(dataset_path.glob("*.parquet"))
                or any(dataset_path.glob("*.npz"))
            ):
                # Validate worker access
                if self._validate_dataset_access(str(dataset_path)):
                    return str(dataset_path)

        # If no dataset found, return None to indicate user needs to provide it
        return None

    def _validate_dataset_access(self, dataset_path: str) -> bool:
        """Validate that workers can access the dataset path."""
        try:
            path = Path(dataset_path)

            # Check if path exists and is readable
            if not path.exists():
                return False

            if path.is_file():
                return path.is_file() and os.access(path, os.R_OK)
            elif path.is_dir():
                return os.access(path, os.R_OK | os.X_OK)

            return False

        except Exception:
            return False

    async def generate_experiment_docs(
        self, config: ExperimentConfig, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate experiment documentation using parallel workers."""

        # Create documentation tasks
        doc_tasks = [
            {
                "task_id": f"setup_doc_{config.experiment_id}",
                "worker_id": "doc_worker_setup",
                "task_description": f"""Generate detailed setup documentation for experiment: {config.name}

                Include:
                - Environment requirements and setup steps
                - Dataset requirements and preprocessing
                - Dependencies and versions
                - Hardware requirements

                Experiment details:
                {json.dumps(config.__dict__, indent=2)}
                """,
                "session_id": session_id,
            },
            {
                "task_id": f"hyperparam_doc_{config.experiment_id}",
                "worker_id": "doc_worker_hyperparam",
                "task_description": f"""Generate hyperparameter documentation for experiment: {config.name}

                Include:
                - Hyperparameter explanations and rationale
                - Expected ranges and sensitivity analysis
                - Scaling considerations for different hardware
                - Reproducibility guidelines (seeds, deterministic ops)

                Hyperparameters:
                {json.dumps(config.hyperparameters or {}, indent=2)}
                """,
                "session_id": session_id,
            },
        ]

        # Create workers for documentation
        for task in doc_tasks:
            worker_id = task["worker_id"]
            if worker_id not in self.workers:
                worker_config = WorkerConfig(
                    worker_id=worker_id,
                    scope_paths=[str(self.experiments_dir), str(self.repo_path)],
                    allowed_tools=["read_file", "edit_file", "run_cmd"],
                    max_cost=1.0,
                    max_iterations=10,
                )
                self.create_worker(worker_config)

        # Execute documentation tasks in parallel
        results = await self.execute_parallel_tasks(doc_tasks)

        # Aggregate results
        documentation = {
            "setup_doc": None,
            "hyperparam_doc": None,
            "generation_success": True,
            "errors": [],
        }

        for result in results:
            if result.success:
                if "setup_doc" in result.task_id:
                    documentation["setup_doc"] = result.result
                elif "hyperparam_doc" in result.task_id:
                    documentation["hyperparam_doc"] = result.result
            else:
                documentation["generation_success"] = False
                documentation["errors"].append(f"{result.task_id}: {result.error}")

        return documentation

    async def run_experiment(
        self, config: ExperimentConfig, session_id: Optional[str] = None
    ) -> ExperimentResult:
        """Run a scaled, singular experiment with machine-aware parameters."""

        start_time = time.time()

        if self.on_experiment_start_callback:
            self.on_experiment_start_callback(config)

        try:
            # Detect machine specs if not already done
            if not self.machine_specs:
                self._detect_machine_specs()

            # Scale experiment parameters
            scaled_params = self._scale_experiment_params(
                config.hyperparameters or {}, self.machine_specs
            )

            # Validate dataset access
            if config.dataset_path and not self._validate_dataset_access(
                config.dataset_path
            ):
                raise Exception(f"Cannot access dataset at {config.dataset_path}")

            # Create experiment worker
            worker_id = f"experiment_worker_{config.experiment_id}"
            if worker_id not in self.workers:
                # Allow access to experiment directory and dataset
                scope_paths = [str(self.experiments_dir)]
                if config.dataset_path:
                    scope_paths.append(str(Path(config.dataset_path).parent))

                worker_config = WorkerConfig(
                    worker_id=worker_id,
                    scope_paths=scope_paths,
                    allowed_tools=["read_file", "edit_file", "run_cmd"],
                    max_cost=5.0,
                    max_iterations=50,
                )
                self.create_worker(worker_config)

            # Prepare experiment execution task
            experiment_task = {
                "task_id": f"experiment_{config.experiment_id}",
                "worker_id": worker_id,
                "task_description": f"""Execute ML experiment: {config.name}

                Description: {config.description}
                Dataset: {config.dataset_path or 'Not specified'}

                Scaled Parameters:
                {json.dumps(scaled_params, indent=2)}

                Requirements:
                - Use scaled parameters appropriate for this machine
                - Log all metrics and outputs to experiment directory
                - Save model checkpoints and artifacts
                - Handle errors gracefully with detailed logging
                - Respect sandbox limits: {self.sandbox_limits}

                Machine Specs:
                {json.dumps(self.machine_specs.__dict__ if self.machine_specs else {}, indent=2)}
                """,
                "context": {
                    "experiment_config": config.__dict__,
                    "scaled_params": scaled_params,
                    "machine_specs": (
                        self.machine_specs.__dict__ if self.machine_specs else {}
                    ),
                    "sandbox_limits": self.sandbox_limits,
                },
                "session_id": session_id,
            }

            # Execute experiment
            task_result = await self.execute_task(**experiment_task)

            execution_time = time.time() - start_time

            # Create experiment result
            experiment_result = ExperimentResult(
                experiment_id=config.experiment_id,
                success=task_result.success,
                metrics=(
                    task_result.result.get("metrics", {}) if task_result.success else {}
                ),
                logs=task_result.result.get("logs", []) if task_result.success else [],
                artifacts=(
                    task_result.result.get("artifacts", [])
                    if task_result.success
                    else []
                ),
                error=task_result.error,
                execution_time=execution_time,
                scaled_params=scaled_params,
            )

            # Store in history
            self.experiment_history.append(experiment_result)

            # Update session with experiment results
            if session_id and self.session_manager:
                session = self.session_manager.load_session(session_id)
                if session:
                    session.metadata.setdefault("experiments", []).append(
                        {
                            "experiment_id": config.experiment_id,
                            "result": experiment_result.__dict__,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                    await self.session_manager._save_session_to_disk(session)

            if self.on_experiment_complete_callback:
                self.on_experiment_complete_callback(experiment_result)

            return experiment_result

        except Exception as e:
            execution_time = time.time() - start_time

            experiment_result = ExperimentResult(
                experiment_id=config.experiment_id,
                success=False,
                error=str(e),
                execution_time=execution_time,
                scaled_params=config.hyperparameters or {},
            )

            self.experiment_history.append(experiment_result)

            if self.on_experiment_complete_callback:
                self.on_experiment_complete_callback(experiment_result)

            return experiment_result

    async def coordinate_research_workflow(
        self,
        research_question: str,
        initial_config: Optional[ExperimentConfig] = None,
        max_iterations: int = 5,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Coordinate complete research workflow with iterative experimentation."""

        workflow_results = {
            "research_question": research_question,
            "iterations": [],
            "total_experiments": 0,
            "successful_experiments": 0,
            "total_cost": 0.0,
            "total_time": 0.0,
            "final_recommendations": [],
        }

        current_config = initial_config
        start_time = time.time()

        for iteration in range(max_iterations):
            iteration_start = time.time()
            iteration_result = {
                "iteration": iteration + 1,
                "conversation": None,
                "documentation": None,
                "experiment": None,
                "analysis": None,
                "next_steps": None,
            }

            try:
                # Step 1: User conversation to refine experiment
                if not current_config:
                    # Generate initial experiment config through conversation
                    conversation_task = {
                        "task_id": f"conversation_iter_{iteration}",
                        "worker_id": "conversation_worker",
                        "task_description": f"""Engage in conversation about research question: {research_question}

                        Generate an experiment configuration that addresses:
                        - Specific hypothesis to test
                        - Required dataset and preprocessing
                        - Appropriate hyperparameters
                        - Success metrics and evaluation criteria

                        Previous iterations: {len(workflow_results['iterations'])}
                        """,
                        "session_id": session_id,
                    }

                    # Create conversation worker if needed
                    if "conversation_worker" not in self.workers:
                        worker_config = WorkerConfig(
                            worker_id="conversation_worker",
                            scope_paths=[
                                str(self.repo_path),
                                str(self.experiments_dir),
                            ],
                            allowed_tools=["read_file", "ask_supervisor"],
                            max_cost=1.0,
                            max_iterations=10,
                        )
                        self.create_worker(worker_config)

                    conv_result = await self.execute_task(**conversation_task)
                    iteration_result["conversation"] = conv_result.result

                    # Parse conversation result to create config
                    current_config = ExperimentConfig(
                        experiment_id=f"exp_{iteration}_{int(time.time())}",
                        name=f"Research Iteration {iteration + 1}",
                        description=research_question,
                        hyperparameters={
                            "batch_size": 32,
                            "epochs": 10,
                            "learning_rate": 0.001,
                        },
                    )

                # Step 2: Check for dataset
                if not current_config.dataset_path:
                    dataset_path = await self._prompt_for_dataset(current_config.name)
                    if not dataset_path:
                        iteration_result["next_steps"] = (
                            "Dataset required - please provide dataset path"
                        )
                        workflow_results["iterations"].append(iteration_result)
                        break
                    current_config.dataset_path = dataset_path

                # Step 3: Generate documentation
                docs = await self.generate_experiment_docs(current_config, session_id)
                iteration_result["documentation"] = docs

                # Step 4: Run experiment
                experiment_result = await self.run_experiment(
                    current_config, session_id
                )
                iteration_result["experiment"] = experiment_result.__dict__
                workflow_results["total_experiments"] += 1

                if experiment_result.success:
                    workflow_results["successful_experiments"] += 1

                # Step 5: Analyze results and determine next steps
                analysis_task = {
                    "task_id": f"analysis_iter_{iteration}",
                    "worker_id": "analysis_worker",
                    "task_description": f"""Analyze experiment results and determine next steps:

                    Research Question: {research_question}
                    Experiment Result: {json.dumps(experiment_result.__dict__, indent=2)}

                    Provide:
                    - Analysis of results and key findings
                    - Recommendations for next experiment (if any)
                    - Whether research question has been sufficiently addressed
                    """,
                    "session_id": session_id,
                }

                # Create analysis worker if needed
                if "analysis_worker" not in self.workers:
                    worker_config = WorkerConfig(
                        worker_id="analysis_worker",
                        scope_paths=[str(self.experiments_dir)],
                        allowed_tools=["read_file", "run_cmd"],
                        max_cost=1.0,
                        max_iterations=10,
                    )
                    self.create_worker(worker_config)

                analysis_result = await self.execute_task(**analysis_task)
                iteration_result["analysis"] = analysis_result.result

                # Determine if we should continue
                if analysis_result.success and analysis_result.result:
                    analysis_text = str(analysis_result.result).lower()
                    if (
                        "sufficient" in analysis_text
                        or "complete" in analysis_text
                        or "no further" in analysis_text
                    ):
                        iteration_result["next_steps"] = "Research complete"
                        workflow_results["iterations"].append(iteration_result)
                        break
                    else:
                        iteration_result["next_steps"] = "Continue with next iteration"
                        # Prepare next iteration config based on analysis
                        current_config = None  # Reset to generate new config

                iteration_result["iteration_time"] = time.time() - iteration_start
                workflow_results["iterations"].append(iteration_result)

            except Exception as e:
                iteration_result["error"] = str(e)
                iteration_result["iteration_time"] = time.time() - iteration_start
                workflow_results["iterations"].append(iteration_result)
                break

        # Aggregate final results
        workflow_results["total_time"] = time.time() - start_time
        workflow_results["total_cost"] = self.total_cost

        # Generate final recommendations
        if workflow_results["successful_experiments"] > 0:
            workflow_results["final_recommendations"] = [
                f"Completed {workflow_results['successful_experiments']} successful experiments",
                f"Total research time: {workflow_results['total_time']:.2f} seconds",
                f"Total cost: ${workflow_results['total_cost']:.4f}",
            ]

        return workflow_results

    def get_research_status(self) -> Dict[str, Any]:
        """Get comprehensive research orchestrator status."""
        base_status = self.get_orchestrator_status()

        research_status = {
            **base_status,
            "orchestrator_type": "research",
            "machine_specs": (
                self.machine_specs.__dict__ if self.machine_specs else None
            ),
            "scale_factor": self.scale_factor,
            "experiments_dir": str(self.experiments_dir),
            "current_experiment": (
                self.current_experiment.__dict__ if self.current_experiment else None
            ),
            "experiment_history_count": len(self.experiment_history),
            "successful_experiments": sum(
                1 for exp in self.experiment_history if exp.success
            ),
            "failed_experiments": sum(
                1 for exp in self.experiment_history if not exp.success
            ),
            "sandbox_limits": self.sandbox_limits,
        }

        return research_status

    def set_research_callbacks(
        self,
        on_experiment_start: Optional[Callable] = None,
        on_experiment_complete: Optional[Callable] = None,
        on_machine_detected: Optional[Callable] = None,
        **base_callbacks,
    ):
        """Set research-specific callback functions."""
        self.on_experiment_start_callback = on_experiment_start
        self.on_experiment_complete_callback = on_experiment_complete
        self.on_machine_detected_callback = on_machine_detected

        # Set base callbacks
        self.set_callbacks(**base_callbacks)


# Convenience function for creating research orchestrator
def create_research_orchestrator(
    scale_factor: float = 1.0,
    experiments_dir: str = "./experiments",
    max_concurrent_workers: int = 3,
    global_cost_limit: float = 20.0,  # Higher default for research
    max_total_iterations: int = 200,  # Higher default for research
    sandbox_limits: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> ResearchOrchestrator:
    """
    Convenience function to create a research orchestrator with research-optimized defaults.

    Args:
        scale_factor: Global scaling factor for experiment parameters
        experiments_dir: Directory to store experiment results
        max_concurrent_workers: Max parallel workers
        global_cost_limit: Cost limit across all workers
        max_total_iterations: Max iterations across all workers
        sandbox_limits: Execution limits for safety
        **kwargs: Additional arguments passed to ResearchOrchestrator

    Returns:
        Configured ResearchOrchestrator instance
    """
    return ResearchOrchestrator(
        scale_factor=scale_factor,
        experiments_dir=experiments_dir,
        max_concurrent_workers=max_concurrent_workers,
        global_cost_limit=global_cost_limit,
        max_total_iterations=max_total_iterations,
        sandbox_limits=sandbox_limits,
        **kwargs,
    )
