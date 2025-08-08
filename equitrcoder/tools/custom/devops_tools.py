"""
DevOps tools for deployment, containerization, and infrastructure management.
"""

import subprocess
import yaml
from pathlib import Path
from typing import Type, Dict
from pydantic import BaseModel, Field

from ..base import Tool, ToolResult
from ...core.unified_config import get_config


class DockerBuildArgs(BaseModel):
    dockerfile_path: str = Field(default="Dockerfile", description="Path to Dockerfile")
    image_name: str = Field(..., description="Name for the Docker image")
    tag: str = Field(default="latest", description="Tag for the Docker image")
    build_context: str = Field(default=".", description="Build context directory")
    build_args: Dict[str, str] = Field(default_factory=dict, description="Build arguments")


class DockerBuild(Tool):
    def get_name(self) -> str:
        return "docker_build"

    def get_description(self) -> str:
        return "Build Docker images from Dockerfiles"

    def get_args_schema(self) -> Type[BaseModel]:
        return DockerBuildArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)
            
            # Check if Dockerfile exists
            dockerfile_path = Path(args.dockerfile_path)
            if not dockerfile_path.exists():
                return ToolResult(success=False, error=f"Dockerfile not found: {args.dockerfile_path}")
            
            # Build docker command
            cmd = [
                "docker", "build",
                "-f", args.dockerfile_path,
                "-t", f"{args.image_name}:{args.tag}"
            ]
            
            # Add build args
            for key, value in args.build_args.items():
                cmd.extend(["--build-arg", f"{key}={value}"])
            
            cmd.append(args.build_context)
            
            # Run docker build
            timeout = get_config('limits.devops_timeout', 600)
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return ToolResult(
                success=result.returncode == 0,
                data={
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode,
                    "command": " ".join(cmd),
                    "image_name": f"{args.image_name}:{args.tag}"
                },
                error=result.stderr if result.returncode != 0 else None
            )
            
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error="Docker build timed out after 10 minutes")
        except FileNotFoundError:
            return ToolResult(success=False, error="Docker not found. Please install Docker first.")
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class CreateDockerfileArgs(BaseModel):
    base_image: str = Field(default="python:3.11-slim", description="Base Docker image")
    working_dir: str = Field(default="/app", description="Working directory in container")
    requirements_file: str = Field(default="requirements.txt", description="Requirements file to copy")
    main_command: str = Field(default="python app.py", description="Main command to run")
    expose_port: int = Field(default=8000, description="Port to expose")


class CreateDockerfile(Tool):
    def get_name(self) -> str:
        return "create_dockerfile"

    def get_description(self) -> str:
        return "Generate a Dockerfile for Python applications"

    def get_args_schema(self) -> Type[BaseModel]:
        return CreateDockerfileArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)
            
            # Generate Dockerfile content
            dockerfile_content = f"""# Generated Dockerfile
FROM {args.base_image}

# Set working directory
WORKDIR {args.working_dir}

# Copy requirements and install dependencies
COPY {args.requirements_file} .
RUN pip install --no-cache-dir -r {args.requirements_file}

# Copy application code
COPY . .

# Expose port
EXPOSE {args.expose_port}

# Run the application
CMD ["{args.main_command.split()[0]}", "{' '.join(args.main_command.split()[1:])}"]
"""
            
            # Write Dockerfile
            dockerfile_path = Path("Dockerfile")
            dockerfile_path.write_text(dockerfile_content)
            
            return ToolResult(
                success=True,
                data={
                    "dockerfile_path": str(dockerfile_path),
                    "content": dockerfile_content,
                    "base_image": args.base_image,
                    "exposed_port": args.expose_port
                }
            )
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class GenerateK8sManifestArgs(BaseModel):
    app_name: str = Field(..., description="Application name")
    image_name: str = Field(..., description="Docker image name")
    port: int = Field(default=8000, description="Application port")
    replicas: int = Field(default=3, description="Number of replicas")
    namespace: str = Field(default="default", description="Kubernetes namespace")


class GenerateK8sManifest(Tool):
    def get_name(self) -> str:
        return "generate_k8s_manifest"

    def get_description(self) -> str:
        return "Generate Kubernetes deployment and service manifests"

    def get_args_schema(self) -> Type[BaseModel]:
        return GenerateK8sManifestArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)
            
            # Generate deployment manifest
            deployment = {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {
                    "name": args.app_name,
                    "namespace": args.namespace
                },
                "spec": {
                    "replicas": args.replicas,
                    "selector": {
                        "matchLabels": {
                            "app": args.app_name
                        }
                    },
                    "template": {
                        "metadata": {
                            "labels": {
                                "app": args.app_name
                            }
                        },
                        "spec": {
                            "containers": [{
                                "name": args.app_name,
                                "image": args.image_name,
                                "ports": [{
                                    "containerPort": args.port
                                }]
                            }]
                        }
                    }
                }
            }
            
            # Generate service manifest
            service = {
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {
                    "name": f"{args.app_name}-service",
                    "namespace": args.namespace
                },
                "spec": {
                    "selector": {
                        "app": args.app_name
                    },
                    "ports": [{
                        "protocol": "TCP",
                        "port": 80,
                        "targetPort": args.port
                    }],
                    "type": "ClusterIP"
                }
            }
            
            # Write manifests to files
            deployment_file = Path(f"{args.app_name}-deployment.yaml")
            service_file = Path(f"{args.app_name}-service.yaml")
            
            with open(deployment_file, 'w') as f:
                yaml.dump(deployment, f, default_flow_style=False)
            
            with open(service_file, 'w') as f:
                yaml.dump(service, f, default_flow_style=False)
            
            return ToolResult(
                success=True,
                data={
                    "deployment_file": str(deployment_file),
                    "service_file": str(service_file),
                    "app_name": args.app_name,
                    "replicas": args.replicas,
                    "namespace": args.namespace
                }
            )
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class CheckSystemResourcesArgs(BaseModel):
    include_disk: bool = Field(default=True, description="Include disk usage information")
    include_memory: bool = Field(default=True, description="Include memory usage information")
    include_cpu: bool = Field(default=True, description="Include CPU usage information")


class CheckSystemResources(Tool):
    def get_name(self) -> str:
        return "check_system_resources"

    def get_description(self) -> str:
        return "Check system resources (CPU, memory, disk usage)"

    def get_args_schema(self) -> Type[BaseModel]:
        return CheckSystemResourcesArgs

    async def run(self, **kwargs) -> ToolResult:
        try:
            args = self.validate_args(kwargs)
            
            resource_info = {}
            
            # Get CPU information
            if args.include_cpu:
                try:
                    # Get CPU usage
                    cpu_result = subprocess.run(
                        ["top", "-bn1"], 
                        capture_output=True, 
                        text=True, 
                        timeout=10
                    )
                    if cpu_result.returncode == 0:
                        # Parse CPU usage from top output
                        lines = cpu_result.stdout.split('\n')
                        for line in lines:
                            if 'Cpu(s):' in line:
                                resource_info['cpu'] = line.strip()
                                break
                except (subprocess.SubprocessError, OSError, Exception):
                    resource_info['cpu'] = "CPU information unavailable"
            
            # Get memory information
            if args.include_memory:
                try:
                    mem_result = subprocess.run(
                        ["free", "-h"], 
                        capture_output=True, 
                        text=True, 
                        timeout=10
                    )
                    if mem_result.returncode == 0:
                        resource_info['memory'] = mem_result.stdout
                except (subprocess.SubprocessError, OSError, Exception):
                    resource_info['memory'] = "Memory information unavailable"
            
            # Get disk information
            if args.include_disk:
                try:
                    disk_result = subprocess.run(
                        ["df", "-h"], 
                        capture_output=True, 
                        text=True, 
                        timeout=10
                    )
                    if disk_result.returncode == 0:
                        resource_info['disk'] = disk_result.stdout
                except (subprocess.SubprocessError, OSError, Exception):
                    resource_info['disk'] = "Disk information unavailable"
            
            return ToolResult(
                success=True,
                data=resource_info
            )
            
        except Exception as e:
            return ToolResult(success=False, error=str(e))