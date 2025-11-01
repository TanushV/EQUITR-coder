from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import yaml
from pydantic import BaseModel, Field

from ...core.unified_config import get_config
from ...providers.litellm import LiteLLMProvider, Message
from ..base import Tool, ToolResult
from ..builtin.shell import RunCommand


class HardwareInfoArgs(BaseModel):
    detailed: bool = Field(
        default=True, description="Include detailed fields when available"
    )


class HardwareInfo(Tool):
    def get_name(self) -> str:
        return "hardware_info"

    def get_description(self) -> str:
        return "Detect and report local hardware and environment details (OS, CPU, RAM, GPU if available)."

    def get_args_schema(self) -> Type[BaseModel]:
        return HardwareInfoArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            self.validate_args(kwargs)

            info: Dict[str, Any] = {}
            # OS / Platform
            info["os"] = platform.platform()
            info["python_version"] = platform.python_version()
            info["architecture"] = platform.machine()
            info["processor"] = platform.processor() or platform.uname().processor

            # CPU count
            try:
                import multiprocessing

                info["cpu_count"] = multiprocessing.cpu_count()
            except Exception:
                pass

            # Memory detection (no psutil dependency)
            mem_total_bytes: Optional[int] = None
            try:
                if hasattr(os, "sysconf"):
                    if os.sysconf_names.get("SC_PAGE_SIZE") and os.sysconf_names.get(
                        "SC_PHYS_PAGES"
                    ):
                        mem_total_bytes = int(os.sysconf("SC_PAGE_SIZE")) * int(
                            os.sysconf("SC_PHYS_PAGES")
                        )
            except Exception:
                pass

            if mem_total_bytes is None:
                # Try vm_stat on macOS
                try:
                    out = subprocess.run(
                        ["/usr/bin/vm_stat"], capture_output=True, text=True
                    )
                    if out.returncode == 0:
                        _ = next(
                            (
                                line
                                for line in out.stdout.splitlines()
                                if "Pages free" in line
                            ),
                            None,
                        )
                        page_size_line = next(
                            (
                                line
                                for line in out.stdout.splitlines()
                                if "page size of" in line
                            ),
                            None,
                        )
                        if page_size_line:
                            _ = int(
                                page_size_line.split("page size of")[-1]
                                .strip()
                                .split()[0]
                            )
                        else:
                            _ = 4096  # default page size
                        # vm_stat doesn't give total pages; fallback to system_profiler
                        sp = subprocess.run(
                            ["/usr/sbin/sysctl", "hw.memsize"],
                            capture_output=True,
                            text=True,
                        )
                        if sp.returncode == 0 and ":" in sp.stdout:
                            mem_total_bytes = int(sp.stdout.split(":")[-1].strip())
                except Exception:
                    pass

            if mem_total_bytes is not None:
                info["memory_total_bytes"] = mem_total_bytes
                info["memory_total_gb"] = round(mem_total_bytes / (1024**3), 2)

            # GPU detection
            gpu_info: Dict[str, Any] = {}
            try:
                if shutil.which("nvidia-smi"):
                    q = [
                        "nvidia-smi",
                        "--query-gpu=name,memory.total,driver_version",
                        "--format=csv,noheader,nounits",
                    ]
                    res = subprocess.run(q, capture_output=True, text=True)
                    if res.returncode == 0:
                        lines = [
                            line.strip()
                            for line in res.stdout.splitlines()
                            if line.strip()
                        ]
                        gpus = []
                        for line in lines:
                            parts = [p.strip() for p in line.split(",")]
                            if len(parts) >= 2:
                                gpus.append(
                                    {
                                        "name": parts[0],
                                        "memory_mb": (
                                            int(parts[1])
                                            if parts[1].isdigit()
                                            else parts[1]
                                        ),
                                        "driver_version": (
                                            parts[2] if len(parts) > 2 else None
                                        ),
                                    }
                                )
                        gpu_info["nvidia"] = gpus
                else:
                    # macOS integrated GPU info
                    if platform.system().lower() == "darwin":
                        sp = subprocess.run(
                            [
                                "/usr/sbin/system_profiler",
                                "SPDisplaysDataType",
                            ],
                            capture_output=True,
                            text=True,
                        )
                        if sp.returncode == 0:
                            models = []
                            for raw_line in sp.stdout.splitlines():
                                if (
                                    "Chipset Model:" in raw_line
                                    or "Chipset Model" in raw_line
                                ):
                                    models.append(raw_line.split(":", 1)[-1].strip())
                            if models:
                                gpu_info["apple_displays"] = models
            except Exception:
                pass

            info["gpu"] = gpu_info

            return ToolResult(success=True, data=info)
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class CreateNotebookArgs(BaseModel):
    path: str = Field(..., description="Path to write the .ipynb file")
    cells: List[str] = Field(
        default_factory=list, description="List of code cell sources"
    )
    kernel_name: str = Field(
        default="python3", description="Kernel name for the notebook"
    )


class CreateNotebook(Tool):
    def get_name(self) -> str:
        return "create_notebook"

    def get_description(self) -> str:
        return "Create a minimal Jupyter notebook (.ipynb) with provided code cells."

    def get_args_schema(self) -> Type[BaseModel]:
        return CreateNotebookArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)
            nb_path = Path(args.path)
            nb_path.parent.mkdir(parents=True, exist_ok=True)

            notebook = {
                "cells": [
                    {
                        "cell_type": "code",
                        "metadata": {},
                        "source": cell,
                        "outputs": [],
                        "execution_count": None,
                    }
                    for cell in args.cells
                ],
                "metadata": {
                    "kernelspec": {
                        "name": args.kernel_name,
                        "display_name": args.kernel_name,
                    }
                },
                "nbformat": 4,
                "nbformat_minor": 5,
            }

            nb_path.write_text(json.dumps(notebook, indent=2), encoding="utf-8")
            return ToolResult(
                success=True, data={"path": str(nb_path), "cells": len(args.cells)}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class RunNotebookArgs(BaseModel):
    path: str = Field(..., description="Path to the notebook file (.ipynb)")
    timeout: int = Field(default=600, description="Execution timeout in seconds")


class RunNotebook(Tool):
    def get_name(self) -> str:
        return "run_notebook"

    def get_description(self) -> str:
        return "Execute a Jupyter notebook and save executed output to a new file. Prefers nbclient, falls back to nbconvert if available."

    def get_args_schema(self) -> Type[BaseModel]:
        return RunNotebookArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)
            nb_path = Path(args.path)
            if not nb_path.exists():
                return ToolResult(success=False, error=f"Notebook not found: {nb_path}")

            executed_path = nb_path.with_name(nb_path.stem + "-executed.ipynb")
            start = time.time()
            # Try nbclient first (preferred)
            try:
                import nbformat  # type: ignore
                from nbclient import NotebookClient  # type: ignore

                nb = nbformat.read(nb_path, as_version=4)
                kernel = (
                    nb.metadata.get("kernelspec", {}).get("name")
                    if isinstance(nb.metadata, dict)
                    else None
                ) or "python3"
                client = NotebookClient(nb, timeout=args.timeout, kernel_name=kernel)
                client.execute()
                nbformat.write(client.nb, executed_path)
                duration = round(time.time() - start, 2)
                return ToolResult(
                    success=True,
                    data={
                        "executed_path": str(executed_path),
                        "duration_sec": duration,
                        "engine": "nbclient",
                    },
                )
            except ImportError:
                # Fall back to nbconvert via jupyter CLI
                if shutil.which("jupyter"):
                    cmd = [
                        "jupyter",
                        "nbconvert",
                        "--to",
                        "notebook",
                        "--execute",
                        "--ExecutePreprocessor.timeout={}".format(args.timeout),
                        "--output",
                        str(executed_path.name),
                        str(nb_path),
                    ]
                    proc = subprocess.run(
                        cmd, cwd=str(nb_path.parent), capture_output=True, text=True
                    )
                    duration = round(time.time() - start, 2)
                    if proc.returncode == 0 and executed_path.exists():
                        return ToolResult(
                            success=True,
                            data={
                                "executed_path": str(executed_path),
                                "duration_sec": duration,
                                "engine": "nbconvert",
                                "stdout": proc.stdout,
                            },
                        )
                    return ToolResult(
                        success=False,
                        error=f"nbconvert failed (code {proc.returncode})",
                        data={"stdout": proc.stdout, "stderr": proc.stderr},
                    )
                else:
                    return ToolResult(
                        success=False,
                        error=(
                            "Notebook execution requires either 'nbclient' and 'nbformat' packages or the 'jupyter' CLI. "
                            "Please install with: pip install nbclient nbformat jupyter"
                        ),
                    )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class RunExperimentsArgs(BaseModel):
    config_path: str = Field(..., description="Path to experiments YAML file")
    stop_on_fail: bool = Field(
        default=False, description="Stop after the first failing experiment"
    )
    results_path: Optional[str] = Field(
        default=None, description="Optional path to write JSON results"
    )


class RunExperiments(Tool):
    def get_name(self) -> str:
        return "run_experiments"

    def get_description(self) -> str:
        return "Run a sequence of shell-based experiments described in a YAML config and report pass/fail."

    def get_args_schema(self) -> Type[BaseModel]:
        return RunExperimentsArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)
            cfg_path = Path(args.config_path)
            if not cfg_path.exists():
                return ToolResult(
                    success=False, error=f"Experiments config not found: {cfg_path}"
                )

            cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
            experiments: List[Dict[str, Any]] = cfg.get("experiments", [])
            if not isinstance(experiments, list) or not experiments:
                return ToolResult(
                    success=False, error="No experiments defined in config"
                )

            # NEW: Global/local requirements for venv bootstrap
            # Accept either a string or list under top-level 'requirements'
            reqs_global: List[str] = []
            top_reqs = cfg.get("requirements")
            if isinstance(top_reqs, str):
                reqs_global = [top_reqs]
            elif isinstance(top_reqs, list):
                reqs_global = [str(x) for x in top_reqs]

            results: List[Dict[str, Any]] = []
            all_passed = True

            # Determine sandbox mode
            sandbox_type = get_config("sandbox.type", "local")
            use_venv = sandbox_type == "venv"
            runner = RunCommand()

            # Prepare logs directory and default results path
            logs_dir = (cfg_path.parent / "logs").resolve()
            try:
                logs_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            default_results_path = (
                cfg_path.parent / "experiments_results.json"
            ).resolve()

            # Hardware-aware configuration
            try:
                from .research_tools import HardwareInfo  # self import safe

                hw = await HardwareInfo().run(detailed=True)
                hw_data = hw.data if hw.success else {}
                cpu_count = int(hw_data.get("cpu_count", 1) or 1)
                mem_gb = float(hw_data.get("memory_total_gb", 4) or 4)
                is_mac = str(hw_data.get("os", "")).lower().find("darwin") >= 0
            except Exception:
                cpu_count = 1
                mem_gb = 4.0
                is_mac = False

            from datetime import datetime as _dt

            for idx, exp in enumerate(experiments, start=1):
                name = exp.get("name") or exp.get("id") or f"exp_{len(results)+1}"
                command = exp.get("command")
                if not command:
                    results.append(
                        {"name": name, "error": "Missing command", "passed": False}
                    )
                    all_passed = False
                    if args.stop_on_fail:
                        break
                    continue
                cwd = exp.get("cwd") or str(cfg_path.parent)
                # Tune timeout by hardware (scale up on low CPU/memory)
                base_timeout = int(exp.get("timeout", 900))
                scale = 1.0
                if cpu_count <= 2:
                    scale *= 1.5
                if mem_gb <= 8:
                    scale *= 1.3
                timeout = int(base_timeout * scale)

                # Per-experiment requirements (string or list), overrides + extends global
                reqs_local: List[str] = []
                exp_reqs = exp.get("requirements")
                if isinstance(exp_reqs, str):
                    reqs_local = [exp_reqs]
                elif isinstance(exp_reqs, list):
                    reqs_local = [str(x) for x in exp_reqs]

                # If none specified, auto-detect requirements.txt in cwd
                req_paths: List[Path] = []
                req_candidates: List[str] = reqs_local + reqs_global
                if not req_candidates:
                    default_req = Path(cwd) / "requirements.txt"
                    if default_req.exists():
                        req_paths.append(default_req)
                # Add any specified requirements, resolved relative to cwd if not absolute
                for r in req_candidates:
                    rp = Path(r)
                    if not rp.is_absolute():
                        rp = Path(cwd) / rp
                    if rp.exists():
                        req_paths.append(rp)

                # Optional pre-commands (setup) before main command
                pre_cmds: List[str] = []
                if isinstance(exp.get("pre"), list):
                    pre_cmds = [str(c) for c in exp.get("pre")]

                # Build one-liner to ensure venv installs happen inside the same ephemeral session
                install_snippets: List[str] = []
                if use_venv and req_paths:
                    for rp in req_paths:
                        install_snippets.append(f"pip install -r '{rp}'")
                # Compose the final command with pre + optional installs
                segments: List[str] = []
                segments.extend(pre_cmds)
                if install_snippets:
                    segments.extend(install_snippets)
                segments.append(command)
                combined = " && ".join(segments)

                # Respect cwd by inlining cd; honor sandbox via use_venv
                full_cmd = f"cd {cwd} && {combined}"
                # Hardware hints: set env vars to let scripts know and to parallelize safely
                env_prefix = f"EQUITR_CPU_COUNT={cpu_count} EQUITR_MEM_GB={int(mem_gb)} EQUITR_IS_MAC={'1' if is_mac else '0'} "
                full_cmd = env_prefix + full_cmd
                tr = await runner.run(
                    command=full_cmd, timeout=timeout, use_venv=use_venv
                )
                rc = (tr.data or {}).get("return_code", 1) if tr.success else 1
                stdout = (tr.data or {}).get("stdout", "") if tr.data else ""
                stderr = (tr.data or {}).get("stderr", tr.error or "")

                passed = rc == 0
                all_passed = all_passed and passed

                # Persist combined logs to file
                timestamp = _dt.utcnow().strftime("%Y%m%d_%H%M%S")
                run_id = f"{idx}_{timestamp}"
                log_path = logs_dir / f"{run_id}.log"
                try:
                    with log_path.open("w", encoding="utf-8", newline="\n") as f:
                        if stdout:
                            f.write("STDOUT:\n")
                            f.write(stdout)
                            if not stdout.endswith("\n"):
                                f.write("\n")
                        if stderr:
                            f.write("STDERR:\n")
                            f.write(stderr)
                            if not stderr.endswith("\n"):
                                f.write("\n")
                except Exception:
                    pass

                result_entry = {
                    "name": name,
                    "command": command,
                    "cwd": cwd,
                    "return_code": rc,
                    "passed": passed,
                    "stdout": stdout[-4000:],
                    "stderr": (stderr or "")[-4000:],
                    "run_id": run_id,
                    "log_path": str(log_path),
                }

                results.append(result_entry)

                if args.stop_on_fail and not passed:
                    break

            # Optionally persist results to disk (JSON)
            try:
                results_target = getattr(args, "results_path", None) or str(
                    default_results_path
                )
                outp = Path(results_target)
                outp.parent.mkdir(parents=True, exist_ok=True)
                payload = {"all_passed": all_passed, "results": results}
                outp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            except Exception:
                pass

            # Force-update experiments.yaml with last_run info and links
            try:
                updated_cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
                updated_exps: List[Dict[str, Any]] = (
                    updated_cfg.get("experiments", []) or []
                )
                # Align per index
                for i, exp in enumerate(updated_exps):
                    if i < len(results):
                        r = results[i]
                        exp["last_run"] = {
                            "timestamp": _dt.utcnow().isoformat(),
                            "run_id": r.get("run_id"),
                            "return_code": r.get("return_code"),
                            "passed": r.get("passed"),
                            "cwd": r.get("cwd"),
                            "log_path": str(Path(r.get("log_path", "")).resolve()),
                            "results_json": str(outp.resolve()),
                        }
                        updated_exps[i] = exp
                updated_cfg["experiments"] = updated_exps
                updated_cfg["last_run_at"] = _dt.utcnow().isoformat()
                cfg_path.write_text(
                    yaml.safe_dump(updated_cfg, sort_keys=False), encoding="utf-8"
                )
            except Exception:
                pass

            return ToolResult(
                success=True,
                data={
                    "all_passed": all_passed,
                    "results": results,
                    "results_path": str(outp),
                },
            )
        except subprocess.TimeoutExpired as te:
            return ToolResult(success=False, error=f"Experiment timed out: {te}")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class WriteAndRunExperimentScriptArgs(BaseModel):
    output_path: str = Field(
        default="run_experiments.py",
        description="Path to write the experiment runner script",
    )
    config_path: str = Field(
        default="docs/experiments.yaml", description="Path to experiments.yaml"
    )


class WriteAndRunExperimentScript(Tool):
    def get_name(self) -> str:
        return "write_and_run_experiment_script"

    def get_description(self) -> str:
        return "Writes a Python script that loads experiments.yaml and executes all experiments, then runs it."

    def get_args_schema(self) -> Type[BaseModel]:
        return WriteAndRunExperimentScriptArgs

    async def run(self, **kwargs) -> ToolResult:
        args = self.validate_args(kwargs)
        try:
            from pathlib import Path

            script_src = f"""
import subprocess, sys, json
from pathlib import Path
import yaml
cfg = Path(r"{args.config_path}")
exp = yaml.safe_load(cfg.read_text(encoding='utf-8')) or {{}}
results = []
for e in exp.get('experiments', []):
    cmd = e.get('command')
    if not cmd:
        continue
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    results.append({{'name': e.get('name'), 'command': cmd, 'return_code': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}})
Path('docs/experiment_results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
print('EXPERIMENTS_DONE')
""".strip()
            out = Path(args.output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(script_src, encoding="utf-8")
            import subprocess

            run = subprocess.run(
                [sys.executable, str(out)], capture_output=True, text=True
            )
            return ToolResult(
                success=(run.returncode == 0),
                data={"stdout": run.stdout, "stderr": run.stderr, "script": str(out)},
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GenerateResearchReportArgs(BaseModel):
    output_path: str = Field(..., description="Path to write the Markdown report")
    task_description: Optional[str] = Field(
        default="", description="High-level task description"
    )
    experiments_config_path: Optional[str] = Field(
        default=None, description="Path to experiments.yaml (optional)"
    )
    results_path: Optional[str] = Field(
        default=None,
        description="Path to JSON results produced by run_experiments (optional)",
    )
    research_plan_path: Optional[str] = Field(
        default=None,
        description="Path to research_plan.yaml for datasets/hardware (optional)",
    )


class GenerateResearchReport(Tool):
    def get_name(self) -> str:
        return "generate_research_report"

    def get_description(self) -> str:
        return "Generate a concise Markdown research report using datasets, hardware, and experiment results. Uses LLM if available."

    def get_args_schema(self) -> Type[BaseModel]:
        return GenerateResearchReportArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)
            output_path = Path(args.output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Load research context
            datasets = []
            hardware: Dict[str, Any] = {}
            try:
                if args.research_plan_path:
                    rp = Path(args.research_plan_path)
                    if rp.exists():
                        plan = yaml.safe_load(rp.read_text(encoding="utf-8")) or {}
                        datasets = plan.get("datasets", []) or []
                        hardware = plan.get("hardware", {}) or {}
            except Exception:
                pass

            if not hardware:
                # Fallback to live hardware detection
                hw_res = await HardwareInfo().run(detailed=True)
                hardware = hw_res.data if hw_res.success else {}

            # Load experiment results
            exp_summary: Dict[str, Any] = {"all_passed": None, "results": []}
            try:
                if args.results_path and Path(args.results_path).exists():
                    exp_summary = json.loads(
                        Path(args.results_path).read_text(encoding="utf-8")
                    )
            except Exception:
                pass

            # Compose report via LLM
            try:
                supervisor_model = get_config("orchestrator.supervisor_model", "gpt-4")
                provider = LiteLLMProvider(model=supervisor_model)
                datasets_txt = "\n".join(
                    f"- {d.get('path')} — {d.get('description','')}" for d in datasets
                )
                system_prompt = (
                    "You are a strict research supervisor. Produce a concise Markdown report summarizing the task, "
                    "datasets, hardware, experiments executed, and outcomes. Include a Conclusion and Next Steps."
                )
                user_prompt = (
                    f"TASK DESCRIPTION:\n{(args.task_description or '').strip()}\n\n"
                    f"DATASETS:\n{datasets_txt or 'N/A'}\n\n"
                    f"HARDWARE (JSON):\n```json\n{json.dumps(hardware, indent=2)}\n```\n\n"
                    f"EXPERIMENT SUMMARY (JSON):\n```json\n{json.dumps(exp_summary, indent=2)}\n```\n\n"
                    "Output ONLY GitHub-Flavored Markdown."
                )
                messages = [
                    Message(role="system", content=system_prompt),
                    Message(role="user", content=user_prompt),
                ]
                resp = await provider.chat(messages=messages)
                md = resp.content.strip()
                if not md.startswith("#"):
                    md = f"# Research Report\n\n{md}"
            except Exception as e:
                # Fallback minimal report
                md = (
                    f"# Research Report\n\n{(args.task_description or '').strip()}\n\n"
                    f"## Datasets\n{(os.linesep).join([str(x) for x in datasets]) or 'N/A'}\n\n"
                    f"## Hardware\n```json\n{json.dumps(hardware, indent=2)}\n```\n\n"
                    f"## Experiments\n```json\n{json.dumps(exp_summary, indent=2)}\n```\n"
                    f"_Report generation fallback: {e}_\n"
                )

            output_path.write_text(md, encoding="utf-8")
            return ToolResult(success=True, data={"output_path": str(output_path)})
        except Exception as e:
            return ToolResult(success=False, error=str(e))
