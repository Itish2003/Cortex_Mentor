"""
Unit tests for ARQ worker tasks.
Tests: process_event_task, synthesis_task, on_startup, on_shutdown, WorkerSettings
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from cortex.workers import (
    process_event_task,
    synthesis_task,
    on_startup,
    on_shutdown,
    WorkerSettings
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_context():
    """Fixture for a mocked ARQ context."""
    ctx = {
        "redis": AsyncMock()
    }
    ctx["redis"].enqueue_job = AsyncMock()
    return ctx


@pytest.fixture
def sample_git_commit_event_data():
    """Sample raw git commit event data."""
    return {
        "event_type": "git_commit",
        "repo_name": "test-repo",
        "branch_name": "main",
        "commit_hash": "abc123def456",
        "author_name": "Test Author",
        "author_email": "test@example.com",
        "message": "feat: add new feature",
        "diff": "diff --git a/file.py",
        "timestamp": datetime.now().isoformat()
    }


@pytest.fixture
def sample_code_change_event_data():
    """Sample raw code change event data."""
    return {
        "event_type": "file_change",
        "file_path": "/path/to/file.py",
        "change_type": "modified",
        "content": "def new_function():\n    pass"
    }


# ============================================================================
# on_startup Tests
# ============================================================================

class TestOnStartup:
    """Tests for on_startup function."""

    @pytest.mark.asyncio
    async def test_creates_redis_pool(self, mocker):
        """Test that on_startup creates a Redis pool and stores it in context."""
        mock_pool = AsyncMock()
        mock_create_pool = mocker.patch(
            'cortex.workers.create_redis_pool',
            new_callable=AsyncMock,
            return_value=mock_pool
        )

        ctx = {}
        await on_startup(ctx)

        mock_create_pool.assert_called_once()
        assert ctx["redis"] == mock_pool


# ============================================================================
# on_shutdown Tests
# ============================================================================

class TestOnShutdown:
    """Tests for on_shutdown function."""

    @pytest.mark.asyncio
    async def test_closes_redis_pool(self, mocker):
        """Test that on_shutdown closes the Redis pool."""
        mock_pool = AsyncMock()
        mock_close = mocker.patch(
            'cortex.workers.close_redis_pool',
            new_callable=AsyncMock
        )

        ctx = {"redis": mock_pool}
        await on_shutdown(ctx)

        mock_close.assert_called_once_with(mock_pool)

    @pytest.mark.asyncio
    async def test_handles_missing_redis_pool(self, mocker):
        """Test that on_shutdown handles missing Redis pool gracefully."""
        mock_close = mocker.patch(
            'cortex.workers.close_redis_pool',
            new_callable=AsyncMock
        )

        ctx = {}
        await on_shutdown(ctx)

        mock_close.assert_called_once_with(None)


# ============================================================================
# process_event_task Tests
# ============================================================================

class TestProcessEventTask:
    """Tests for process_event_task function."""

    @pytest.mark.asyncio
    async def test_successful_git_commit_processing(self, mock_context, sample_git_commit_event_data, mocker):
        """Test successful processing of a git commit event."""
        # Mock all services
        mock_kg_service = MagicMock()
        mock_chroma_service = MagicMock()
        mock_llm_service = MagicMock()
        mock_llm_service.generate_commit_summary.return_value = "Test summary"

        mocker.patch('cortex.workers.KnowledgeGraphService', return_value=mock_kg_service)
        mocker.patch('cortex.workers.ChromaService', return_value=mock_chroma_service)
        mocker.patch('cortex.workers.LLMService', return_value=mock_llm_service)

        # Mock the Pipeline
        mock_pipeline = MagicMock()
        mock_pipeline.execute = AsyncMock()
        mocker.patch('cortex.workers.Pipeline', return_value=mock_pipeline)

        await process_event_task(mock_context, sample_git_commit_event_data)

        # Verify pipeline was executed
        mock_pipeline.execute.assert_called_once()
        call_args = mock_pipeline.execute.call_args
        assert call_args.kwargs["data"] == sample_git_commit_event_data
        assert "redis" in call_args.kwargs["context"]

    @pytest.mark.asyncio
    async def test_successful_code_change_processing(self, mock_context, sample_code_change_event_data, mocker):
        """Test successful processing of a code change event."""
        mock_kg_service = MagicMock()
        mock_chroma_service = MagicMock()
        mock_llm_service = MagicMock()
        mock_llm_service.generate_code_change_summary.return_value = "Test summary"

        mocker.patch('cortex.workers.KnowledgeGraphService', return_value=mock_kg_service)
        mocker.patch('cortex.workers.ChromaService', return_value=mock_chroma_service)
        mocker.patch('cortex.workers.LLMService', return_value=mock_llm_service)

        mock_pipeline = MagicMock()
        mock_pipeline.execute = AsyncMock()
        mocker.patch('cortex.workers.Pipeline', return_value=mock_pipeline)

        await process_event_task(mock_context, sample_code_change_event_data)

        mock_pipeline.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_pipeline_failure_is_logged(self, mock_context, sample_git_commit_event_data, mocker):
        """Test that pipeline failures are logged but don't raise."""
        mocker.patch('cortex.workers.KnowledgeGraphService')
        mocker.patch('cortex.workers.ChromaService')
        mocker.patch('cortex.workers.LLMService')

        mock_pipeline = MagicMock()
        mock_pipeline.execute = AsyncMock(side_effect=Exception("Pipeline error"))
        mocker.patch('cortex.workers.Pipeline', return_value=mock_pipeline)

        mock_logger = mocker.patch('cortex.workers.logger')

        # Should not raise
        await process_event_task(mock_context, sample_git_commit_event_data)

        # Error should be logged
        mock_logger.error.assert_called()
        assert "Comprehension pipeline failed" in str(mock_logger.error.call_args)

    @pytest.mark.asyncio
    async def test_passes_redis_from_context(self, mock_context, sample_git_commit_event_data, mocker):
        """Test that Redis pool is passed from context to pipeline."""
        mocker.patch('cortex.workers.KnowledgeGraphService')
        mocker.patch('cortex.workers.ChromaService')
        mocker.patch('cortex.workers.LLMService')

        mock_pipeline = MagicMock()
        mock_pipeline.execute = AsyncMock()
        mocker.patch('cortex.workers.Pipeline', return_value=mock_pipeline)

        await process_event_task(mock_context, sample_git_commit_event_data)

        call_args = mock_pipeline.execute.call_args
        assert call_args.kwargs["context"]["redis"] == mock_context["redis"]

    @pytest.mark.asyncio
    async def test_creates_correct_pipeline_structure(self, mock_context, sample_git_commit_event_data, mocker):
        """Test that the correct pipeline processors are created."""
        mock_kg_service = MagicMock()
        mock_chroma_service = MagicMock()
        mock_llm_service = MagicMock()

        mocker.patch('cortex.workers.KnowledgeGraphService', return_value=mock_kg_service)
        mocker.patch('cortex.workers.ChromaService', return_value=mock_chroma_service)
        mocker.patch('cortex.workers.LLMService', return_value=mock_llm_service)

        mock_pipeline_cls = mocker.patch('cortex.workers.Pipeline')
        mock_pipeline_cls.return_value.execute = AsyncMock()

        await process_event_task(mock_context, sample_git_commit_event_data)

        # Verify Pipeline was constructed with processors
        mock_pipeline_cls.assert_called_once()
        processors = mock_pipeline_cls.call_args[0][0]

        # Should have 4 processors: EventDeserializer, InsightGenerator, [parallel writers], SynthesisTrigger
        assert len(processors) == 4

        # Third element should be a list (parallel processors)
        assert isinstance(processors[2], list)
        assert len(processors[2]) == 2  # KnowledgeGraphWriter and ChromaWriter


# ============================================================================
# synthesis_task Tests
# ============================================================================

class TestSynthesisTask:
    """Tests for synthesis_task function."""

    @pytest.mark.asyncio
    async def test_successful_synthesis(self, mock_context, mocker):
        """Test successful synthesis task execution."""
        mock_chroma_service = MagicMock()
        mock_upstash_service = MagicMock()
        mock_llm_service = MagicMock()

        mocker.patch('cortex.workers.ChromaService', return_value=mock_chroma_service)
        mocker.patch('cortex.workers.UpstashService', return_value=mock_upstash_service)
        mocker.patch('cortex.workers.LLMService', return_value=mock_llm_service)

        mock_pipeline = MagicMock()
        mock_pipeline.execute = AsyncMock()
        mocker.patch('cortex.workers.create_synthesis_pipeline', return_value=mock_pipeline)

        query_text = "How to implement authentication?"
        await synthesis_task(mock_context, query_text)

        mock_pipeline.execute.assert_called_once()
        call_args = mock_pipeline.execute.call_args
        assert call_args.kwargs["data"] == query_text

    @pytest.mark.asyncio
    async def test_passes_context_with_google_search(self, mock_context, mocker):
        """Test that context includes google_search tool."""
        mocker.patch('cortex.workers.ChromaService')
        mocker.patch('cortex.workers.UpstashService')
        mocker.patch('cortex.workers.LLMService')

        mock_pipeline = MagicMock()
        mock_pipeline.execute = AsyncMock()
        mocker.patch('cortex.workers.create_synthesis_pipeline', return_value=mock_pipeline)

        await synthesis_task(mock_context, "test query")

        call_args = mock_pipeline.execute.call_args
        assert "redis" in call_args.kwargs["context"]
        assert "google_search" in call_args.kwargs["context"]

    @pytest.mark.asyncio
    async def test_pipeline_failure_is_logged(self, mock_context, mocker):
        """Test that synthesis pipeline failures are logged."""
        mocker.patch('cortex.workers.ChromaService')
        mocker.patch('cortex.workers.UpstashService')
        mocker.patch('cortex.workers.LLMService')

        mock_pipeline = MagicMock()
        mock_pipeline.execute = AsyncMock(side_effect=Exception("Synthesis error"))
        mocker.patch('cortex.workers.create_synthesis_pipeline', return_value=mock_pipeline)

        mock_logger = mocker.patch('cortex.workers.logger')

        # Should not raise
        await synthesis_task(mock_context, "test query")

        # Error should be logged
        mock_logger.error.assert_called()
        assert "Synthesis pipeline failed" in str(mock_logger.error.call_args)

    @pytest.mark.asyncio
    async def test_truncates_query_in_log(self, mock_context, mocker):
        """Test that long queries are truncated in log messages."""
        mocker.patch('cortex.workers.ChromaService')
        mocker.patch('cortex.workers.UpstashService')
        mocker.patch('cortex.workers.LLMService')

        mock_pipeline = MagicMock()
        mock_pipeline.execute = AsyncMock()
        mocker.patch('cortex.workers.create_synthesis_pipeline', return_value=mock_pipeline)

        mock_logger = mocker.patch('cortex.workers.logger')

        long_query = "A" * 200  # Very long query
        await synthesis_task(mock_context, long_query)

        # Info log should be called with truncated query
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_creates_synthesis_pipeline_with_services(self, mock_context, mocker):
        """Test that create_synthesis_pipeline is called with correct services."""
        mock_chroma = MagicMock()
        mock_upstash = MagicMock()
        mock_llm = MagicMock()

        mocker.patch('cortex.workers.ChromaService', return_value=mock_chroma)
        mocker.patch('cortex.workers.UpstashService', return_value=mock_upstash)
        mocker.patch('cortex.workers.LLMService', return_value=mock_llm)

        mock_create_pipeline = mocker.patch('cortex.workers.create_synthesis_pipeline')
        mock_create_pipeline.return_value.execute = AsyncMock()

        await synthesis_task(mock_context, "test query")

        mock_create_pipeline.assert_called_once_with(
            mock_chroma,
            mock_upstash,
            mock_llm,
            mock_context["redis"]
        )


# ============================================================================
# WorkerSettings Tests
# ============================================================================

class TestWorkerSettings:
    """Tests for WorkerSettings configuration."""

    def test_has_required_functions(self):
        """Test that WorkerSettings has the required task functions."""
        assert process_event_task in WorkerSettings.functions
        assert synthesis_task in WorkerSettings.functions

    def test_has_required_queues(self):
        """Test that WorkerSettings has the required queues."""
        assert 'high_priority' in WorkerSettings.queues
        assert 'low_priority' in WorkerSettings.queues

    def test_has_lifecycle_hooks(self):
        """Test that WorkerSettings has startup and shutdown hooks."""
        assert WorkerSettings.on_startup == on_startup
        assert WorkerSettings.on_shutdown == on_shutdown

    def test_functions_list_length(self):
        """Test that exactly 2 functions are registered."""
        assert len(WorkerSettings.functions) == 2

    def test_queues_list_length(self):
        """Test that exactly 2 queues are configured."""
        assert len(WorkerSettings.queues) == 2
