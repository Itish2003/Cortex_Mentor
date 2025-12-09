"""
Unit tests for curation pipeline processors.
Tests: UpstashWriter, CurationProcessor, create_curation_agent
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import uuid

from cortex.pipelines.curation import (
    UpstashWriter,
    CurationProcessor,
    create_curation_agent
)
from cortex.services.upstash_service import UpstashService
from cortex.services.llmservice import LLMService
from cortex.core.config import Settings


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_upstash_service():
    """Fixture for a mocked UpstashService."""
    service = MagicMock(spec=UpstashService)
    service.add_document = AsyncMock()
    return service


@pytest.fixture
def mock_llm_service():
    """Fixture for a mocked LLMService."""
    mock_settings = MagicMock(spec=Settings)
    mock_settings.gemini_flash_model = "gemini-flash-test"
    mock_settings.gemini_pro_model = "gemini-pro-test"

    service = MagicMock(spec=LLMService)
    service.settings = mock_settings
    return service


# ============================================================================
# UpstashWriter Tests
# ============================================================================

class TestUpstashWriter:
    """Tests for UpstashWriter class."""

    @pytest.mark.asyncio
    async def test_write_success(self, mock_upstash_service):
        """Test successful write to Upstash."""
        writer = UpstashWriter(mock_upstash_service)
        data = "Test curated content"

        result = await writer.write(data)

        assert result == "Successfully wrote data to Upstash."
        mock_upstash_service.add_document.assert_called_once()

        # Verify the call arguments
        call_args = mock_upstash_service.add_document.call_args
        assert call_args.kwargs["content"] == data
        assert call_args.kwargs["metadata"] == {"source": "web_search_curation"}
        assert "doc_id" in call_args.kwargs

    @pytest.mark.asyncio
    async def test_write_sets_has_written_flag(self, mock_upstash_service):
        """Test that write sets the _has_written flag."""
        writer = UpstashWriter(mock_upstash_service)

        assert writer._has_written is False
        await writer.write("Test data")
        assert writer._has_written is True

    @pytest.mark.asyncio
    async def test_write_duplicate_prevention(self, mock_upstash_service):
        """Test that duplicate writes are prevented."""
        writer = UpstashWriter(mock_upstash_service)

        # First write
        result1 = await writer.write("First data")
        assert result1 == "Successfully wrote data to Upstash."

        # Second write (should be blocked)
        result2 = await writer.write("Second data")
        assert result2 == "TerminateProcess: Duplicate write attempt."

        # Verify only one write occurred
        assert mock_upstash_service.add_document.call_count == 1

    @pytest.mark.asyncio
    async def test_write_error_handling(self, mock_upstash_service):
        """Test error handling during write."""
        mock_upstash_service.add_document.side_effect = Exception("Upstash error")
        writer = UpstashWriter(mock_upstash_service)

        result = await writer.write("Test data")

        assert "Failed to write data to Upstash" in result
        assert "Upstash error" in result
        # Flag should not be set on failure
        assert writer._has_written is False

    @pytest.mark.asyncio
    async def test_write_generates_unique_doc_ids(self, mock_upstash_service):
        """Test that each write generates a unique document ID."""
        # Create two writers to test separate writes
        writer1 = UpstashWriter(mock_upstash_service)
        writer2 = UpstashWriter(mock_upstash_service)

        await writer1.write("Data 1")
        await writer2.write("Data 2")

        # Get the doc_ids from both calls
        call1_doc_id = mock_upstash_service.add_document.call_args_list[0].kwargs["doc_id"]
        call2_doc_id = mock_upstash_service.add_document.call_args_list[1].kwargs["doc_id"]

        assert call1_doc_id != call2_doc_id


# ============================================================================
# CurationProcessor Tests
# ============================================================================

class TestCurationProcessor:
    """Tests for CurationProcessor."""

    @pytest.mark.asyncio
    async def test_process_success(self, mock_upstash_service, mock_llm_service, mocker):
        """Test successful curation process."""
        # Mock the agent creation and execution
        mock_agent = MagicMock()
        mocker.patch(
            'cortex.pipelines.curation.create_curation_agent',
            return_value=mock_agent
        )
        mocker.patch(
            'cortex.pipelines.curation.run_standalone_agent',
            new_callable=AsyncMock,
            return_value="Curated knowledge summary"
        )

        processor = CurationProcessor(mock_upstash_service, mock_llm_service)
        data = {"query_text": "How to implement authentication?"}

        result = await processor.process(data, {})

        assert result["query_text"] == "How to implement authentication?"
        assert result["augmented_knowledge"] == "Curated knowledge summary"

    @pytest.mark.asyncio
    async def test_process_creates_new_agent_per_request(self, mock_upstash_service, mock_llm_service, mocker):
        """Test that a new agent is created for each request (avoids session state reuse)."""
        mock_create_agent = mocker.patch(
            'cortex.pipelines.curation.create_curation_agent',
            return_value=MagicMock()
        )
        mocker.patch(
            'cortex.pipelines.curation.run_standalone_agent',
            new_callable=AsyncMock,
            return_value="Result"
        )

        processor = CurationProcessor(mock_upstash_service, mock_llm_service)

        # Process twice
        await processor.process({"query_text": "Query 1"}, {})
        await processor.process({"query_text": "Query 2"}, {})

        # Verify create_curation_agent was called twice (once per request)
        assert mock_create_agent.call_count == 2

    @pytest.mark.asyncio
    async def test_process_passes_correct_target_agent(self, mock_upstash_service, mock_llm_service, mocker):
        """Test that the correct target agent name is passed."""
        mock_agent = MagicMock()
        mocker.patch('cortex.pipelines.curation.create_curation_agent', return_value=mock_agent)
        mock_run_agent = mocker.patch(
            'cortex.pipelines.curation.run_standalone_agent',
            new_callable=AsyncMock,
            return_value="Result"
        )

        processor = CurationProcessor(mock_upstash_service, mock_llm_service)
        await processor.process({"query_text": "Test query"}, {})

        mock_run_agent.assert_called_once_with(
            mock_agent,
            "Test query",
            target_agent_name="chief_editor"
        )


# ============================================================================
# create_curation_agent Tests
# ============================================================================

class TestCreateCurationAgent:
    """Tests for create_curation_agent factory function."""

    def test_creates_sequential_agent(self, mock_upstash_service, mock_llm_service, mocker):
        """Test that create_curation_agent returns a SequentialAgent."""
        from google.adk.agents import LlmAgent

        # Mock the google search agent with an actual LlmAgent mock
        mock_web_searcher = LlmAgent(
            name="mock_web_searcher",
            instruction="Mock web searcher",
            model="gemini-flash-test"
        )
        mocker.patch('cortex.pipelines.curation.create_google_search_agent', return_value=mock_web_searcher)
        mocker.patch('cortex.pipelines.curation.PromptManager')

        agent = create_curation_agent(mock_upstash_service, mock_llm_service)

        assert agent.name == "curation_agent"
        # The agent should have 3 sub-agents: web_searcher, parallel_analyzer, chief_editor
        assert len(agent.sub_agents) == 3

    def test_creates_parallel_analyzer(self, mock_upstash_service, mock_llm_service, mocker):
        """Test that the parallel analyzer contains security and best practices analysts."""
        from google.adk.agents import LlmAgent

        mock_web_searcher = LlmAgent(
            name="mock_web_searcher",
            instruction="Mock web searcher",
            model="gemini-flash-test"
        )
        mocker.patch('cortex.pipelines.curation.create_google_search_agent', return_value=mock_web_searcher)
        mocker.patch('cortex.pipelines.curation.PromptManager')

        agent = create_curation_agent(mock_upstash_service, mock_llm_service)

        # The second sub-agent should be the parallel_analyzer
        parallel_analyzer = agent.sub_agents[1]
        assert parallel_analyzer.name == "parallel_analyzer"

        # It should have 2 sub-agents: security_analyst and best_practices_analyst
        analyst_names = [a.name for a in parallel_analyzer.sub_agents]
        assert "security_analyst" in analyst_names
        assert "best_practices_analyst" in analyst_names

    def test_chief_editor_has_upstash_tool(self, mock_upstash_service, mock_llm_service, mocker):
        """Test that the chief editor has the UpstashWriter tool."""
        from google.adk.agents import LlmAgent

        mock_web_searcher = LlmAgent(
            name="mock_web_searcher",
            instruction="Mock web searcher",
            model="gemini-flash-test"
        )
        mocker.patch('cortex.pipelines.curation.create_google_search_agent', return_value=mock_web_searcher)
        mocker.patch('cortex.pipelines.curation.PromptManager')

        agent = create_curation_agent(mock_upstash_service, mock_llm_service)

        # The third sub-agent should be the chief_editor
        chief_editor = agent.sub_agents[2]
        assert chief_editor.name == "chief_editor"

        # Chief editor should have tools
        assert len(chief_editor.tools) > 0

    def test_uses_correct_models(self, mock_upstash_service, mock_llm_service, mocker):
        """Test that the agents use the correct LLM models from settings."""
        from google.adk.agents import LlmAgent

        mock_web_searcher = LlmAgent(
            name="mock_web_searcher",
            instruction="Mock web searcher",
            model="gemini-flash-test"
        )
        mocker.patch('cortex.pipelines.curation.create_google_search_agent', return_value=mock_web_searcher)
        mocker.patch('cortex.pipelines.curation.PromptManager')

        agent = create_curation_agent(mock_upstash_service, mock_llm_service)

        # Check that the chief_editor uses the pro model
        chief_editor = agent.sub_agents[2]
        assert chief_editor.model == "gemini-pro-test"

        # Check that the analysts use the flash model
        parallel_analyzer = agent.sub_agents[1]
        for analyst in parallel_analyzer.sub_agents:
            assert analyst.model == "gemini-flash-test"
