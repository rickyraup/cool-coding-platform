"""Docker client service for managing containers."""

import logging
import os
from typing import Any, Optional

import docker
from docker.errors import DockerException, ImageNotFound
from docker.models.containers import Container


logger = logging.getLogger(__name__)


class DockerClientService:
    """Service for managing Docker client and basic operations."""

    def __init__(self) -> None:
        self._client: Optional[docker.DockerClient] = None
        self._image_name = (
            "code-platform-python"  # Use custom Python image with pandas, scipy, etc.
        )

    @property
    def client(self) -> docker.DockerClient:
        """Get Docker client instance, creating if needed."""
        if self._client is None:
            try:
                # Try multiple connection methods for compatibility (Docker Desktop priority)
                user = os.getenv("USER", "rickyraup1")
                connection_methods = [
                    # Docker Desktop socket (primary)
                    lambda: docker.DockerClient(
                        base_url=f"unix:///Users/{user}/Library/Containers/com.docker.docker/Data/docker-cli.sock",
                    ),
                    # Alternative Docker Desktop socket
                    lambda: docker.DockerClient(
                        base_url=f"unix:///Users/{user}/.docker/run/docker.sock",
                    ),
                    # Standard Docker socket
                    lambda: docker.DockerClient(base_url="unix://var/run/docker.sock"),
                    # Environment-based connection (last resort)
                    lambda: docker.from_env(),
                ]

                last_error = None
                for method in connection_methods:
                    try:
                        self._client = method()
                        # Test connection
                        self._client.ping()
                        logger.info("Docker client connected successfully")
                        break
                    except Exception as e:
                        last_error = e
                        continue

                if self._client is None:
                    msg = f"Cannot connect to Docker daemon with any method. Last error: {last_error}"
                    raise ConnectionError(
                        msg,
                    )

            except Exception as e:
                logger.exception(f"Failed to connect to Docker: {e}")
                msg = f"Cannot connect to Docker daemon: {e}"
                raise ConnectionError(msg)
        return self._client

    def is_docker_available(self) -> bool:
        """Check if Docker daemon is available and responsive."""
        try:
            self.client.ping()
            return True
        except Exception as e:
            logger.warning(f"Docker not available: {e}")
            return False

    def ensure_image_exists(self) -> bool:
        """Ensure the Python execution image exists, try to build if not."""
        try:
            self.client.images.get(self._image_name)
            logger.info(f"Image {self._image_name} found")
            return True
        except ImageNotFound:
            logger.warning(f"Image {self._image_name} not found")
            return False
        except DockerException as e:
            logger.exception(f"Error checking image: {e}")
            return False

    def get_container_security_config(self) -> dict[str, Any]:
        """Get the security configuration for containers."""
        return {
            "user": "1000:1000",  # Non-root user
            "read_only": False,  # Allow write access for pip installations
            "security_opt": ["no-new-privileges"],
            "mem_limit": "512m",
            "memswap_limit": "512m",
            "cpu_count": 1,
            "pids_limit": 100,  # Increased for pip operations
            "network_mode": "bridge",  # Allow network access for pip
            "remove": True,  # Auto-remove when stopped
            "detach": True,  # Run in background
            "tmpfs": {
                "/tmp": "rw,size=100m",  # Writable tmp directory
            },
        }

    def create_session_container(self, session_id: str, working_dir: str) -> Container:
        """Create a new container for a user session."""
        if not self.ensure_image_exists():
            msg = f"Docker image {self._image_name} not available. Please build the image first."
            raise RuntimeError(
                msg,
            )

        container_name = f"session-{session_id}"

        # Container configuration
        config = self.get_container_security_config()
        config.update(
            {
                "name": container_name,
                "working_dir": "/app",
                "volumes": {working_dir: {"bind": "/app", "mode": "rw"}},
                "environment": {
                    "PYTHONPATH": "/app",
                    "HOME": "/app",
                    "USER": "codeuser",
                },
            },
        )

        try:
            # Run container with a long-running command (sleep) so we can exec into it
            container = self.client.containers.run(
                image=self._image_name,
                command=["sleep", "infinity"],  # Keep container alive
                **config,
            )
            logger.info(
                f"Created container {container.short_id} for session {session_id}",
            )
            return container

        except DockerException as e:
            logger.exception(f"Failed to create container for session {session_id}: {e}")
            msg = f"Container creation failed: {e}"
            raise RuntimeError(msg)

    def get_container(self, container_id: str) -> Optional[Container]:
        """Get container by ID."""
        try:
            return self.client.containers.get(container_id)
        except Exception as e:
            logger.warning(f"Container {container_id} not found: {e}")
            return None

    def stop_container(self, container: Container, timeout: int = 10) -> bool:
        """Stop and remove a container."""
        try:
            container.stop(timeout=timeout)
            logger.info(f"Stopped container {container.short_id}")
            return True
        except Exception as e:
            logger.exception(f"Failed to stop container {container.short_id}: {e}")
            try:
                container.kill()
                logger.info(f"Force killed container {container.short_id}")
                return True
            except Exception as kill_error:
                logger.exception(
                    f"Failed to kill container {container.short_id}: {kill_error}",
                )
                return False

    def execute_command(self, container: Container, command: str) -> tuple[str, int]:
        """Execute a command in the container and return output and exit code."""
        try:
            # Use exec_run for each command instead of persistent shell
            exec_result = container.exec_run(
                cmd=["sh", "-c", command],  # Use sh -c for better compatibility
                stdout=True,
                stderr=True,
                stdin=False,
                tty=False,
                demux=False,
                workdir="/app",
            )

            output = (
                exec_result.output.decode("utf-8", errors="replace")
                if exec_result.output
                else ""
            )
            exit_code = (
                exec_result.exit_code if exec_result.exit_code is not None else 0
            )

            return output, exit_code

        except Exception as e:
            logger.exception(f"Command execution failed: {e}")
            return f"Error executing command: {e}", 1

    def get_container_stats(self, container: Container) -> dict[str, Any]:
        """Get resource usage stats for a container."""
        try:
            stats = container.stats(stream=False)

            # Calculate memory usage in MB
            memory_usage = stats["memory_stats"].get("usage", 0)
            memory_limit = stats["memory_stats"].get("limit", 1)
            memory_mb = memory_usage / (1024 * 1024)

            # Calculate CPU percentage
            cpu_delta = (
                stats["cpu_stats"]["cpu_usage"]["total_usage"]
                - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            )
            system_delta = (
                stats["cpu_stats"]["system_cpu_usage"]
                - stats["precpu_stats"]["system_cpu_usage"]
            )
            cpu_percent = (
                (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0.0
            )

            return {
                "memory_mb": round(memory_mb, 2),
                "memory_limit_mb": round(memory_limit / (1024 * 1024), 2),
                "cpu_percent": round(cpu_percent, 2),
                "container_id": container.short_id,
                "status": container.status,
            }
        except Exception as e:
            logger.exception(f"Failed to get container stats: {e}")
            return {
                "memory_mb": 0,
                "memory_limit_mb": 512,
                "cpu_percent": 0,
                "container_id": container.short_id if container else "unknown",
                "status": "unknown",
            }

    def cleanup_all_session_containers(self) -> int:
        """Clean up all session containers (useful for startup)."""
        try:
            containers = self.client.containers.list(
                all=True, filters={"name": "session-"},
            )

            count = 0
            for container in containers:
                try:
                    container.remove(force=True)
                    count += 1
                    logger.info(f"Cleaned up container {container.short_id}")
                except Exception as e:
                    logger.warning(
                        f"Failed to cleanup container {container.short_id}: {e}",
                    )

            logger.info(f"Cleaned up {count} session containers")
            return count

        except Exception as e:
            logger.exception(f"Failed to cleanup containers: {e}")
            return 0


# Global instance
docker_client_service = DockerClientService()
