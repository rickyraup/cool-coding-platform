"""Kubernetes client service for managing pods."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Optional


try:
    from kubernetes import client, config
    from kubernetes.client import V1PersistentVolumeClaim, V1Pod
    from kubernetes.client.rest import ApiException

    KUBERNETES_AVAILABLE = True
except ImportError:
    client = None
    config = None
    V1Pod = None
    V1PersistentVolumeClaim = None
    ApiException = None
    KUBERNETES_AVAILABLE = False


logger = logging.getLogger(__name__)


@dataclass
class PodSession:
    """Information about an active Kubernetes pod session."""

    name: str
    namespace: str
    pod: V1Pod
    pvc_name: str
    status: str = "pending"


class KubernetesClientService:
    """Service for managing Kubernetes client and pod operations."""

    def __init__(self) -> None:
        self._core_v1_api: Optional[client.CoreV1Api] = None
        self._namespace = os.getenv("KUBERNETES_NAMESPACE", "default")
        self._image_name = os.getenv("EXECUTION_IMAGE", "rraup12/code-execution:latest")
        # Custom image with Python 3.11+, Node.js 20, pandas, scipy, numpy, and other required packages

    @property
    def core_v1_api(self) -> client.CoreV1Api:
        """Get Kubernetes Core V1 API instance, creating if needed."""
        if not KUBERNETES_AVAILABLE or client is None or config is None:
            raise ConnectionError("Kubernetes client library not available")

        if self._core_v1_api is None:
            try:
                # Try in-cluster config first (for production)
                try:
                    config.load_incluster_config()
                    logger.info("Loaded in-cluster Kubernetes config")
                except config.ConfigException:
                    # Fall back to kubeconfig for local development
                    config.load_kube_config()
                    logger.info("Loaded kubeconfig for local development")

                self._core_v1_api = client.CoreV1Api()

            except Exception as e:
                logger.exception(f"Failed to configure Kubernetes client: {e}")
                msg = f"Cannot configure Kubernetes client: {e}"
                raise ConnectionError(msg) from e

        return self._core_v1_api

    def is_kubernetes_available(self) -> bool:
        """Check if Kubernetes API is available and responsive."""
        try:
            # Try to list namespaces as a health check
            self.core_v1_api.list_namespace()
            return True
        except Exception as e:
            logger.warning(f"Kubernetes not available: {e}")
            return False

    def get_pod_security_config(self) -> dict[str, Any]:
        """Get the security configuration for pods - compatible with kind cluster."""
        return {
            "allowPrivilegeEscalation": False,
            "readOnlyRootFilesystem": False,  # Allow write access for pip installations
            "capabilities": {"drop": ["ALL"]},
        }

    def create_pod_spec(self, session_id: str, pvc_name: str) -> dict[str, Any]:
        """Create a pod specification for a user session."""
        # Sanitize session_id to be RFC 1123 compliant (replace underscores with hyphens)
        sanitized_id = session_id.replace("_", "-").lower()
        pod_name = f"session-{sanitized_id}"
        security_config = self.get_pod_security_config()

        # Truncate label value to 63 characters max (Kubernetes label value limit)
        label_value = sanitized_id[:63] if len(sanitized_id) > 63 else sanitized_id

        return {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": pod_name,
                "namespace": self._namespace,
                "labels": {
                    "app": "code-execution",
                    "session-id": label_value,
                    "managed-by": "cool-coding-platform",
                },
            },
            "spec": {
                "containers": [
                    {
                        "name": "code-executor",
                        "image": self._image_name,
                        "command": ["sleep", "infinity"],  # Keep pod alive
                        "workingDir": "/app",
                        "env": [
                            {"name": "PYTHONPATH", "value": "/app"},
                            {"name": "HOME", "value": "/app"},
                            {"name": "USER", "value": "codeuser"},
                            {"name": "NODE_ENV", "value": "development"},
                        ],
                        "resources": {
                            "requests": {"memory": "256Mi", "cpu": "200m"},
                            "limits": {"memory": "512Mi", "cpu": "500m"},
                        },
                        "securityContext": security_config,
                        "volumeMounts": [{"name": "workspace", "mountPath": "/app"}],
                    }
                ],
                "volumes": [
                    {
                        "name": "workspace",
                        "persistentVolumeClaim": {"claimName": pvc_name},
                    }
                ],
                "restartPolicy": "Never",
            },
        }

    def create_pvc_spec(self, session_id: str, size: str = "1Gi") -> dict[str, Any]:
        """Create a PersistentVolumeClaim specification for a user session."""
        # Sanitize session_id to be RFC 1123 compliant (replace underscores with hyphens)
        sanitized_id = session_id.replace("_", "-").lower()
        pvc_name = f"workspace-{sanitized_id}"

        # Truncate label value to 63 characters max (Kubernetes label value limit)
        label_value = sanitized_id[:63] if len(sanitized_id) > 63 else sanitized_id

        return {
            "apiVersion": "v1",
            "kind": "PersistentVolumeClaim",
            "metadata": {
                "name": pvc_name,
                "namespace": self._namespace,
                "labels": {
                    "app": "code-execution",
                    "session-id": label_value,
                    "managed-by": "cool-coding-platform",
                },
            },
            "spec": {
                "accessModes": ["ReadWriteOnce"],
                "resources": {"requests": {"storage": size}},
            },
        }

    async def create_session_pod(self, session_id: str) -> PodSession:
        """Create a new pod for a user session."""
        try:
            # Sanitize session_id to be RFC 1123 compliant
            sanitized_id = session_id.replace("_", "-").lower()
            pvc_name = f"workspace-{sanitized_id}"
            pvc_spec = self.create_pvc_spec(session_id)

            try:
                self.core_v1_api.create_namespaced_persistent_volume_claim(
                    namespace=self._namespace, body=pvc_spec
                )
                logger.info(f"Created PVC {pvc_name} for session {session_id}")
            except ApiException as e:
                if e.status == 409:  # Already exists
                    logger.info(f"PVC {pvc_name} already exists, reusing")
                    self.core_v1_api.read_namespaced_persistent_volume_claim(
                        name=pvc_name, namespace=self._namespace
                    )
                else:
                    raise

            # Create pod with the PVC
            pod_spec = self.create_pod_spec(session_id, pvc_name)
            pod = self.core_v1_api.create_namespaced_pod(
                namespace=self._namespace, body=pod_spec
            )

            logger.info(f"Created pod {pod.metadata.name} for session {session_id}")

            return PodSession(
                name=pod.metadata.name,
                namespace=self._namespace,
                pod=pod,
                pvc_name=pvc_name,
                status=pod.status.phase,
            )

        except ApiException as e:
            logger.exception(f"Failed to create pod for session {session_id}: {e}")
            msg = f"Pod creation failed: {e}"
            raise RuntimeError(msg)

    def get_pod(self, pod_name: str) -> Optional[V1Pod]:
        """Get pod by name."""
        try:
            return self.core_v1_api.read_namespaced_pod(
                name=pod_name, namespace=self._namespace
            )
        except ApiException as e:
            if e.status == 404:
                return None
            logger.warning(f"Pod {pod_name} not found: {e}")
            return None

    def delete_pod(self, pod_name: str) -> bool:
        """Delete a pod."""
        try:
            self.core_v1_api.delete_namespaced_pod(
                name=pod_name, namespace=self._namespace
            )
            logger.info(f"Deleted pod {pod_name}")
            return True
        except ApiException as e:
            if e.status == 404:
                logger.info(f"Pod {pod_name} already deleted")
                return True
            logger.exception(f"Failed to delete pod {pod_name}: {e}")
            return False

    def delete_pvc(self, pvc_name: str) -> bool:
        """Delete a PersistentVolumeClaim."""
        try:
            self.core_v1_api.delete_namespaced_persistent_volume_claim(
                name=pvc_name, namespace=self._namespace
            )
            logger.info(f"Deleted PVC {pvc_name}")
            return True
        except ApiException as e:
            if e.status == 404:
                logger.info(f"PVC {pvc_name} already deleted")
                return True
            logger.exception(f"Failed to delete PVC {pvc_name}: {e}")
            return False

    def copy_files_to_pod(self, pod_name: str, local_dir: str) -> bool:
        """Copy files from local directory to pod's /app directory."""
        try:
            import os
            import tarfile
            import io
            from kubernetes.stream import stream

            if not os.path.exists(local_dir):
                logger.warning(f"Local directory {local_dir} does not exist")
                return False

            # Create a tar archive of the local directory
            tar_buffer = io.BytesIO()
            with tarfile.open(fileobj=tar_buffer, mode='w') as tar:
                for root, dirs, files in os.walk(local_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, local_dir)
                        tar.add(file_path, arcname=arcname)

            tar_buffer.seek(0)
            tar_data = tar_buffer.read()

            # Copy tar archive to pod and extract
            exec_command = ['tar', 'xf', '-', '-C', '/app']

            resp = stream(
                self.core_v1_api.connect_get_namespaced_pod_exec,
                pod_name,
                self._namespace,
                command=exec_command,
                stderr=True,
                stdin=True,
                stdout=True,
                tty=False,
                _preload_content=False
            )

            # Write tar data to stdin
            resp.write_stdin(tar_data)
            resp.close()

            logger.info(f"Copied files from {local_dir} to pod {pod_name}")
            return True

        except Exception as e:
            logger.exception(f"Failed to copy files to pod {pod_name}: {e}")
            return False

    def execute_command(self, pod_name: str, command: str) -> tuple[str, int]:
        """Execute a command in a pod and return output and exit code."""
        try:
            from kubernetes.stream import stream

            # Execute command in the pod
            exec_command = ["/bin/sh", "-c", command]

            resp = stream(
                self.core_v1_api.connect_get_namespaced_pod_exec,
                pod_name,
                self._namespace,
                command=exec_command,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False,
            )

            # For simplicity, return the output as success (exit code 0)
            # In a more advanced implementation, you'd need to capture the actual exit code
            return resp, 0

        except Exception as e:
            logger.exception(f"Command execution failed in pod {pod_name}: {e}")
            return f"Error executing command: {e}", 1

    def get_pod_stats(self, pod_name: str) -> dict[str, Any]:
        """Get resource usage stats for a pod."""
        try:
            pod = self.get_pod(pod_name)
            if not pod:
                return {
                    "memory_mb": 0,
                    "memory_limit_mb": 512,
                    "cpu_percent": 0,
                    "pod_name": pod_name,
                    "status": "not_found",
                }

            # Extract resource limits from pod spec
            container = pod.spec.containers[0]
            memory_limit = container.resources.limits.get("memory", "512Mi")
            container.resources.limits.get("cpu", "500m")

            # Convert memory limit to MB (simplified)
            memory_limit_mb = 512  # Default
            if memory_limit.endswith("Mi"):
                memory_limit_mb = int(memory_limit[:-2])
            elif memory_limit.endswith("Gi"):
                memory_limit_mb = int(memory_limit[:-2]) * 1024

            return {
                "memory_mb": 0,  # Would need metrics server to get actual usage
                "memory_limit_mb": memory_limit_mb,
                "cpu_percent": 0,  # Would need metrics server to get actual usage
                "pod_name": pod_name,
                "status": pod.status.phase,
            }
        except Exception as e:
            logger.exception(f"Failed to get pod stats for {pod_name}: {e}")
            return {
                "memory_mb": 0,
                "memory_limit_mb": 512,
                "cpu_percent": 0,
                "pod_name": pod_name,
                "status": "unknown",
            }

    def cleanup_session_pods(
        self, label_selector: str = "managed-by=cool-coding-platform"
    ) -> int:
        """Clean up all session pods (useful for cleanup)."""
        try:
            # Delete pods
            pods = self.core_v1_api.list_namespaced_pod(
                namespace=self._namespace, label_selector=label_selector
            )

            pod_count = 0
            for pod in pods.items:
                try:
                    self.delete_pod(pod.metadata.name)
                    pod_count += 1
                except Exception as e:
                    logger.warning(f"Failed to cleanup pod {pod.metadata.name}: {e}")

            # Delete PVCs
            pvcs = self.core_v1_api.list_namespaced_persistent_volume_claim(
                namespace=self._namespace, label_selector=label_selector
            )

            pvc_count = 0
            for pvc in pvcs.items:
                try:
                    self.delete_pvc(pvc.metadata.name)
                    pvc_count += 1
                except Exception as e:
                    logger.warning(f"Failed to cleanup PVC {pvc.metadata.name}: {e}")

            logger.info(f"Cleaned up {pod_count} pods and {pvc_count} PVCs")
            return pod_count

        except Exception as e:
            logger.exception(f"Failed to cleanup session pods: {e}")
            return 0


# Global instance
kubernetes_client_service = KubernetesClientService()
