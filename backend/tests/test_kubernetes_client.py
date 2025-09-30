"""Tests for Kubernetes client service."""

import pytest
from unittest.mock import Mock, MagicMock, patch

from app.services.kubernetes_client import KubernetesClientService, PodSession, KUBERNETES_AVAILABLE


@pytest.mark.skipif(not KUBERNETES_AVAILABLE, reason="Kubernetes client library not available")
class TestKubernetesClientService:
    """Test suite for Kubernetes client service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = KubernetesClientService()

    @patch('app.services.kubernetes_client.config')
    @patch('app.services.kubernetes_client.client')
    def test_core_v1_api_initialization_incluster(self, mock_client, mock_config):
        """Test Kubernetes client initialization with in-cluster config."""
        mock_config.load_incluster_config = Mock()
        mock_config.ConfigException = Exception
        mock_client.CoreV1Api = Mock(return_value=Mock())

        # Reset the cached API
        self.service._core_v1_api = None

        api = self.service.core_v1_api

        assert api is not None
        mock_config.load_incluster_config.assert_called_once()
        mock_client.CoreV1Api.assert_called_once()

    @patch('app.services.kubernetes_client.config')
    @patch('app.services.kubernetes_client.client')
    def test_core_v1_api_initialization_kubeconfig_fallback(self, mock_client, mock_config):
        """Test Kubernetes client initialization with kubeconfig fallback."""
        # Simulate in-cluster config failure
        mock_config.ConfigException = Exception
        mock_config.load_incluster_config = Mock(side_effect=Exception("Not in cluster"))
        mock_config.load_kube_config = Mock()
        mock_client.CoreV1Api = Mock(return_value=Mock())

        # Reset the cached API
        self.service._core_v1_api = None

        api = self.service.core_v1_api

        assert api is not None
        mock_config.load_incluster_config.assert_called_once()
        mock_config.load_kube_config.assert_called_once()
        mock_client.CoreV1Api.assert_called_once()

    def test_get_pod_security_config(self):
        """Test pod security configuration."""
        config = self.service.get_pod_security_config()

        assert config["runAsUser"] == 1000
        assert config["runAsGroup"] == 1000
        assert config["runAsNonRoot"] is True
        assert config["allowPrivilegeEscalation"] is False
        assert config["readOnlyRootFilesystem"] is False
        assert "drop" in config["capabilities"]
        assert "ALL" in config["capabilities"]["drop"]

    def test_create_pod_spec(self):
        """Test creating a pod specification."""
        session_id = "test-session-123"
        pvc_name = "workspace-test-session-123"

        spec = self.service.create_pod_spec(session_id, pvc_name)

        assert spec["kind"] == "Pod"
        assert spec["metadata"]["name"] == f"session-{session_id}"
        assert spec["metadata"]["labels"]["session-id"] == session_id
        assert spec["spec"]["containers"][0]["name"] == "code-executor"
        assert spec["spec"]["containers"][0]["workingDir"] == "/app"
        assert spec["spec"]["volumes"][0]["persistentVolumeClaim"]["claimName"] == pvc_name

        # Check resource limits
        resources = spec["spec"]["containers"][0]["resources"]
        assert "requests" in resources
        assert "limits" in resources
        assert resources["limits"]["memory"] == "512Mi"
        assert resources["limits"]["cpu"] == "500m"

    def test_create_pvc_spec(self):
        """Test creating a PVC specification."""
        session_id = "test-session-456"

        spec = self.service.create_pvc_spec(session_id, size="2Gi")

        assert spec["kind"] == "PersistentVolumeClaim"
        assert spec["metadata"]["name"] == f"workspace-{session_id}"
        assert spec["metadata"]["labels"]["session-id"] == session_id
        assert spec["spec"]["accessModes"] == ["ReadWriteOnce"]
        assert spec["spec"]["resources"]["requests"]["storage"] == "2Gi"

    @pytest.mark.asyncio
    @patch.object(KubernetesClientService, 'core_v1_api')
    async def test_create_session_pod_success(self, mock_api):
        """Test successful pod creation."""
        session_id = "test-session-789"
        mock_pod = Mock()
        mock_pod.metadata.name = f"session-{session_id}"
        mock_pod.status.phase = "Pending"

        mock_api.create_namespaced_persistent_volume_claim = Mock(return_value=Mock())
        mock_api.create_namespaced_pod = Mock(return_value=mock_pod)

        pod_session = await self.service.create_session_pod(session_id)

        assert isinstance(pod_session, PodSession)
        assert pod_session.name == f"session-{session_id}"
        assert pod_session.pvc_name == f"workspace-{session_id}"
        assert pod_session.status == "Pending"

        mock_api.create_namespaced_persistent_volume_claim.assert_called_once()
        mock_api.create_namespaced_pod.assert_called_once()

    @pytest.mark.asyncio
    @patch.object(KubernetesClientService, 'core_v1_api')
    async def test_create_session_pod_pvc_already_exists(self, mock_api):
        """Test pod creation when PVC already exists."""
        from kubernetes.client.rest import ApiException

        session_id = "test-session-existing"
        mock_pod = Mock()
        mock_pod.metadata.name = f"session-{session_id}"
        mock_pod.status.phase = "Pending"

        # Simulate PVC already exists (409 Conflict)
        pvc_error = ApiException(status=409)
        mock_api.create_namespaced_persistent_volume_claim = Mock(side_effect=pvc_error)
        mock_api.read_namespaced_persistent_volume_claim = Mock(return_value=Mock())
        mock_api.create_namespaced_pod = Mock(return_value=mock_pod)

        pod_session = await self.service.create_session_pod(session_id)

        assert isinstance(pod_session, PodSession)
        mock_api.read_namespaced_persistent_volume_claim.assert_called_once()
        mock_api.create_namespaced_pod.assert_called_once()

    @patch.object(KubernetesClientService, 'core_v1_api')
    def test_get_pod_success(self, mock_api):
        """Test getting a pod successfully."""
        pod_name = "session-test-pod"
        mock_pod = Mock()
        mock_api.read_namespaced_pod = Mock(return_value=mock_pod)

        result = self.service.get_pod(pod_name)

        assert result == mock_pod
        mock_api.read_namespaced_pod.assert_called_once_with(
            name=pod_name, namespace=self.service._namespace
        )

    @patch.object(KubernetesClientService, 'core_v1_api')
    def test_get_pod_not_found(self, mock_api):
        """Test getting a non-existent pod."""
        from kubernetes.client.rest import ApiException

        pod_name = "nonexistent-pod"
        mock_api.read_namespaced_pod = Mock(side_effect=ApiException(status=404))

        result = self.service.get_pod(pod_name)

        assert result is None

    @patch.object(KubernetesClientService, 'core_v1_api')
    def test_delete_pod_success(self, mock_api):
        """Test deleting a pod successfully."""
        pod_name = "session-delete-test"
        mock_api.delete_namespaced_pod = Mock()

        result = self.service.delete_pod(pod_name)

        assert result is True
        mock_api.delete_namespaced_pod.assert_called_once_with(
            name=pod_name, namespace=self.service._namespace
        )

    @patch.object(KubernetesClientService, 'core_v1_api')
    def test_delete_pod_already_deleted(self, mock_api):
        """Test deleting a pod that's already deleted."""
        from kubernetes.client.rest import ApiException

        pod_name = "already-deleted"
        mock_api.delete_namespaced_pod = Mock(side_effect=ApiException(status=404))

        result = self.service.delete_pod(pod_name)

        assert result is True

    @patch.object(KubernetesClientService, 'core_v1_api')
    def test_delete_pvc_success(self, mock_api):
        """Test deleting a PVC successfully."""
        pvc_name = "workspace-delete-test"
        mock_api.delete_namespaced_persistent_volume_claim = Mock()

        result = self.service.delete_pvc(pvc_name)

        assert result is True
        mock_api.delete_namespaced_persistent_volume_claim.assert_called_once_with(
            name=pvc_name, namespace=self.service._namespace
        )

    @patch.object(KubernetesClientService, 'core_v1_api')
    @patch('kubernetes.stream.stream')
    def test_execute_command_success(self, mock_stream, mock_api):
        """Test executing a command in a pod successfully."""
        pod_name = "session-exec-test"
        command = "python main.py"
        expected_output = "Hello, World!"

        mock_stream.return_value = expected_output

        output, exit_code = self.service.execute_command(pod_name, command)

        assert output == expected_output
        assert exit_code == 0
        mock_stream.assert_called_once()

    @patch.object(KubernetesClientService, 'core_v1_api')
    def test_get_pod_stats(self, mock_api):
        """Test getting pod resource stats."""
        pod_name = "session-stats-test"
        mock_pod = Mock()
        mock_pod.spec.containers = [Mock()]
        mock_pod.spec.containers[0].resources.limits = {"memory": "512Mi", "cpu": "500m"}
        mock_pod.status.phase = "Running"

        mock_api.read_namespaced_pod = Mock(return_value=mock_pod)

        stats = self.service.get_pod_stats(pod_name)

        assert stats["pod_name"] == pod_name
        assert stats["memory_limit_mb"] == 512
        assert stats["status"] == "Running"

    @patch.object(KubernetesClientService, 'core_v1_api')
    def test_get_pod_stats_not_found(self, mock_api):
        """Test getting stats for non-existent pod."""
        from kubernetes.client.rest import ApiException

        pod_name = "nonexistent-stats"
        mock_api.read_namespaced_pod = Mock(side_effect=ApiException(status=404))

        stats = self.service.get_pod_stats(pod_name)

        assert stats["status"] == "not_found"
        assert stats["memory_mb"] == 0

    @patch.object(KubernetesClientService, 'core_v1_api')
    def test_cleanup_session_pods(self, mock_api):
        """Test cleanup of all session pods."""
        # Mock pod list
        mock_pods = Mock()
        mock_pods.items = [
            Mock(metadata=Mock(name="session-1")),
            Mock(metadata=Mock(name="session-2"))
        ]

        # Mock PVC list
        mock_pvcs = Mock()
        mock_pvcs.items = [
            Mock(metadata=Mock(name="workspace-1")),
            Mock(metadata=Mock(name="workspace-2"))
        ]

        mock_api.list_namespaced_pod = Mock(return_value=mock_pods)
        mock_api.list_namespaced_persistent_volume_claim = Mock(return_value=mock_pvcs)
        mock_api.delete_namespaced_pod = Mock()
        mock_api.delete_namespaced_persistent_volume_claim = Mock()

        count = self.service.cleanup_session_pods()

        assert count == 2
        assert mock_api.delete_namespaced_pod.call_count == 2
        assert mock_api.delete_namespaced_persistent_volume_claim.call_count == 2


class TestKubernetesClientWithoutLibrary:
    """Test Kubernetes client behavior when library is not available."""

    @patch('app.services.kubernetes_client.KUBERNETES_AVAILABLE', False)
    def test_core_v1_api_raises_error_when_unavailable(self):
        """Test that accessing API raises error when Kubernetes library unavailable."""
        service = KubernetesClientService()
        service._core_v1_api = None

        with pytest.raises(ConnectionError, match="Kubernetes client library not available"):
            _ = service.core_v1_api