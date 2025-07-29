"""
Integration tests for the programmatic interface
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from equitrcoder import (
    EquitrCoder,
    MultiAgentTaskConfiguration,
    TaskConfiguration,
    create_multi_agent_coder,
    create_single_agent_coder,
)


class TestProgrammaticInterface:
    """Integration tests for the programmatic interface."""

    def test_equitrcoder_instantiation(self):
        """Test basic EquitrCoder instantiation."""
        # Single mode
        coder = EquitrCoder(mode="single")
        assert coder.mode == "single"
        assert coder.git_enabled == True

        # Multi mode
        multi_coder = EquitrCoder(mode="multi", git_enabled=False)
        assert multi_coder.mode == "multi"
        assert multi_coder.git_enabled == False

    def test_task_configuration(self):
        """Test TaskConfiguration creation."""
        config = TaskConfiguration(
            description="Test task",
            max_cost=2.0,
            max_iterations=10,
            model="gpt-4",
            auto_commit=False,
        )

        assert config.description == "Test task"
        assert config.max_cost == 2.0
        assert config.max_iterations == 10
        assert config.model == "gpt-4"
        assert config.auto_commit == False

    def test_multi_agent_task_configuration(self):
        """Test MultiAgentTaskConfiguration creation."""
        config = MultiAgentTaskConfiguration(
            description="Multi-agent task",
            max_workers=3,
            max_cost=10.0,
            supervisor_model="gpt-4",
            worker_model="gpt-3.5-turbo",
        )

        assert config.description == "Multi-agent task"
        assert config.max_workers == 3
        assert config.max_cost == 10.0
        assert config.supervisor_model == "gpt-4"
        assert config.worker_model == "gpt-3.5-turbo"

    def test_check_available_api_keys(self):
        """Test API key availability checking."""
        coder = EquitrCoder()
        keys = coder.check_available_api_keys()

        assert isinstance(keys, dict)
        # Should return empty dict if no keys are set
        assert len(keys) >= 0

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    def test_check_available_api_keys_with_key(self):
        """Test API key checking with key present."""
        coder = EquitrCoder()
        keys = coder.check_available_api_keys()

        assert "openai" in keys
        assert keys["openai"] == True

    async def test_check_model_availability_basic(self):
        """Test basic model availability checking."""
        coder = EquitrCoder()

        # Test with a known model (should return False without API key)
        available = await coder.check_model_availability("gpt-4", test_call=False)
        assert isinstance(available, bool)

    def test_convenience_functions(self):
        """Test convenience factory functions."""
        # Single agent coder
        single_coder = create_single_agent_coder(repo_path=".", git_enabled=True)
        assert single_coder.mode == "single"
        assert single_coder.git_enabled == True

        # Multi agent coder
        multi_coder = create_multi_agent_coder(
            repo_path=".",
            max_workers=2,
            supervisor_model="gpt-4",
            worker_model="gpt-3.5-turbo",
        )
        assert multi_coder.mode == "multi"

    async def test_cleanup(self):
        """Test resource cleanup."""
        coder = EquitrCoder()

        # Should not raise any exceptions
        await coder.cleanup()

    def test_session_management_methods(self):
        """Test session management methods."""
        coder = EquitrCoder()

        # Test session listing (should not crash)
        sessions = coder.list_sessions()
        assert isinstance(sessions, list)

        # Test session history (should return None for non-existent session)
        history = coder.get_session_history("non-existent")
        assert history is None

    def test_git_integration_methods(self):
        """Test git integration methods."""
        coder = EquitrCoder(git_enabled=True)

        # Test git status (should not crash)
        status = coder.get_git_status()
        assert isinstance(status, dict)

        # Test recent commits (should not crash)
        commits = coder.get_recent_commits(5)
        assert isinstance(commits, list)

    def test_git_disabled(self):
        """Test behavior when git is disabled."""
        coder = EquitrCoder(git_enabled=False)

        status = coder.get_git_status()
        assert "error" in status
        assert status["error"] == "Git is disabled"

        commits = coder.get_recent_commits()
        assert commits == []

    async def test_execute_single_task_mock(self):
        """Test single task execution with mocked clean architecture."""
        coder = EquitrCoder(mode="single")

        # Mock the clean architecture run_single_agent_mode function
        with patch(
            "equitrcoder.programmatic.interface.run_single_agent_mode"
        ) as mock_run:
            mock_run.return_value = {
                "success": True,
                "cost": 0.05,
                "iterations": 3,
                "execution_result": {"final_message": "Task completed"},
                "session_id": "test-session",
            }

            config = TaskConfiguration(
                description="Test task", model="gpt-4", max_cost=1.0
            )
            result = await coder.execute_task("Test task", config)

            assert result.success == True
            assert "Task completed" in result.content
            assert result.cost == 0.05
            assert result.iterations == 3

    async def test_invalid_mode(self):
        """Test invalid mode handling."""
        coder = EquitrCoder(mode="invalid")
        result = await coder.execute_task("test")

        # Should return failed result instead of raising exception
        assert result.success == False
        assert "Invalid mode: invalid" in result.error


class TestErrorHandling:
    """Test error handling in programmatic interface."""

    async def test_execute_task_without_config(self):
        """Test task execution without configuration."""
        coder = EquitrCoder(mode="single")

        # Should create default config
        with patch.object(coder, "_execute_single_task") as mock_execute:
            mock_execute.return_value = AsyncMock()
            mock_execute.return_value.success = True

            await coder.execute_task("Test task")

            # Should have been called with None config (config created inside method)
            mock_execute.assert_called_once()
            args = mock_execute.call_args[0]
            assert args[0] == "Test task"
            assert (
                args[1] is None
            )  # Config is None, created inside _execute_single_task

    async def test_execute_task_exception_handling(self):
        """Test exception handling during task execution."""
        coder = EquitrCoder(mode="single")

        with patch.object(
            coder, "_execute_single_task", side_effect=Exception("Test error")
        ):
            result = await coder.execute_task("Test task")

            assert result.success == False
            assert result.error == "Test error"
            assert result.cost == 0.0
            assert result.iterations == 0


if __name__ == "__main__":
    pytest.main([__file__])
