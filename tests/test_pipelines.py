import pytest
from unittest.mock import MagicMock, AsyncMock, call
from cortex.pipelines.synthesis import KnowledgeGatewayProcessor, GatewayDecision, PrivateKnowledgeQuerier, PublicKnowledgeQuerier, CurationTriggerProcessor, InsightSynthesizer, RunPrivatePipeline, RunPublicPipeline
from cortex.pipelines.curation import CurationProcessor # Import CurationProcessor for mocking
from cortex.services.llmservice import LLMService
from cortex.services.prompt_manager import PromptManager
from cortex.services.chroma_service import ChromaService
from cortex.services.upstash_service import UpstashService
from cortex.core.config import Settings
from google.adk.agents import LlmAgent
from cortex.utility.agent_runner import run_standalone_agent # Import for patching
from cortex.pipelines.pipelines import Pipeline
from cortex.pipelines.graph_traversal import GraphTraversalProcessor
from cortex.pipelines.delivery import AudioDeliveryProcessor # New import
from redis.asyncio import Redis # New import for mocking
from google.cloud import texttospeech # New import for mocking
import base64
import json


@pytest.fixture
def mock_llm_service(mocker):
    """Fixture for a mocked LLMService."""
    mock_settings = MagicMock(spec=Settings)
    mock_settings.gemini_pro_model = "gemini-pro-test"
    mock_settings.gemini_flash_model = "gemini-flash-test"
    mock_llm = MagicMock(spec=LLMService)
    mock_llm.settings = mock_settings
    # Do not set generate.return_value here, mock it directly in tests that use it via patch.object
    return mock_llm

@pytest.fixture
def mock_prompt_manager(mocker):
    """Fixture for a mocked PromptManager."""
    mock_pm = MagicMock(spec=PromptManager)
    # No side_effect here, we will set return_value dynamically in tests if needed
    return mock_pm

@pytest.fixture
def mock_settings(mocker):
    """Fixture for a mocked Settings instance."""
    mock_s = MagicMock(spec=Settings)
    mock_s.knowledge_graph_path = "/tmp/test_kg" # Or a suitable path for testing
    mock_s.tts_voice_name = "en-US-Wavenet-D" # For AudioDeliveryProcessor
    return mock_s

@pytest.fixture
def gateway_processor(mock_llm_service, mock_prompt_manager, mocker):
    """Fixture for KnowledgeGatewayProcessor with mocked dependencies."""
    # Patch PromptManager at the module level before instantiating KnowledgeGatewayProcessor
    mocker.patch('cortex.pipelines.synthesis.PromptManager', return_value=mock_prompt_manager)
    return KnowledgeGatewayProcessor(mock_llm_service)

@pytest.mark.asyncio
async def test_knowledge_gateway_processor_needs_improvement_true(gateway_processor, mock_llm_service, mock_prompt_manager, mocker):
    """Test processor when LLM indicates knowledge needs improvement (JSON true)."""
    # Mock run_standalone_agent to return a JSON string indicating true
    mock_run_standalone_agent = mocker.patch(
        'cortex.pipelines.synthesis.run_standalone_agent',
        new_callable=mocker.AsyncMock,
        return_value='{"needs_improvement": true}'
    )

    data = {"query_text": "test query", "public_results": ["result 1", "result 2"]}
    context = {}
    
    # Set return values for prompt_manager.render for this test specifically
    mock_prompt_manager.render.side_effect = ["mocked instruction", "rendered prompt"]

    result = await gateway_processor.process(data, context)
    
    assert result["needs_improvement"] is True
    
    # Assert PromptManager.render calls
    expected_calls = [
        call("knowledge_gateway.jinja2"), # For instruction
        call("knowledge_gateway.jinja2", query_text="test query", public_context="result 1 result 2") # For prompt
    ]
    mock_prompt_manager.render.assert_has_calls(expected_calls)
    
    # Assert run_standalone_agent call
    mock_run_standalone_agent.assert_called_once()
    args, kwargs = mock_run_standalone_agent.call_args
    # Check the agent's instruction and model
    assert isinstance(args[0], LlmAgent)
    assert args[0].instruction == "mocked instruction"
    assert args[0].model == "gemini-flash-test"
    assert args[1] == "rendered prompt"


@pytest.mark.asyncio
async def test_knowledge_gateway_processor_needs_improvement_false(gateway_processor, mock_llm_service, mock_prompt_manager, mocker):
    """Test processor when LLM indicates knowledge is sufficient (JSON false)."""
    mocker.patch(
        'cortex.pipelines.synthesis.run_standalone_agent',
        new_callable=mocker.AsyncMock,
        return_value='{"needs_improvement": false}'
    )

    data = {"query_text": "test query", "public_results": ["result 1"]}
    context = {}
    
    # Set return values for prompt_manager.render for this test specifically
    mock_prompt_manager.render.side_effect = ["mocked instruction", "rendered prompt"]

    result = await gateway_processor.process(data, context)
    
    assert result["needs_improvement"] is False


@pytest.mark.asyncio
async def test_knowledge_gateway_processor_fallback_true(gateway_processor, mock_llm_service, mock_prompt_manager, mocker):
    """Test processor fallback for non-JSON response indicating true."""
    mocker.patch(
        'cortex.pipelines.synthesis.run_standalone_agent',
        new_callable=mocker.AsyncMock,
        return_value='NEEDS_IMPROVEMENT'
    )

    data = {"query_text": "test query", "public_results": []}
    context = {}
    
    # Set return values for prompt_manager.render for this test specifically
    mock_prompt_manager.render.side_effect = ["mocked instruction", "rendered prompt"]

    result = await gateway_processor.process(data, context)
    
    assert result["needs_improvement"] is True


@pytest.mark.asyncio
async def test_knowledge_gateway_processor_fallback_false(gateway_processor, mock_llm_service, mock_prompt_manager, mocker):
    """Test processor fallback for non-JSON response indicating false."""
    mocker.patch(
        'cortex.pipelines.synthesis.run_standalone_agent',
        new_callable=mocker.AsyncMock,
        return_value='some other text'
    )

    data = {"query_text": "test query"}
    context = {}
    
    # Set return values for prompt_manager.render for this test specifically
    mock_prompt_manager.render.side_effect = ["mocked instruction", "rendered prompt"]

    result = await gateway_processor.process(data, context)
    
    assert result["needs_improvement"] is False


@pytest.mark.asyncio
async def test_knowledge_gateway_processor_llm_agent_error(gateway_processor, mock_llm_service, mock_prompt_manager, mocker):
    """Test processor handles errors from the LLM agent and falls back to false."""
    mocker.patch(
        'cortex.pipelines.synthesis.run_standalone_agent',
        new_callable=mocker.AsyncMock,
        side_effect=Exception("LLM agent failed")
    )

    data = {"query_text": "test query"}
    context = {}
    
    # Set return values for prompt_manager.render for this test specifically
    mock_prompt_manager.render.side_effect = ["mocked instruction", "rendered prompt"]

    result = await gateway_processor.process(data, context)
    
    assert result["needs_improvement"] is False

# Tests for PrivateKnowledgeQuerier
@pytest.fixture
def mock_chroma_service(mocker):
    """Fixture for a mocked ChromaService."""
    mock_cs = MagicMock(spec=ChromaService)
    # Mimic the structure of results from ChromaService.query
    mock_cs.query.return_value = {
        "documents": [["doc1_content", "doc2_content"]],
        "metadatas": [[
            {"file_path": "/path/to/file1.py", "other": "meta1"},
            {"file_path": "/path/to/file2.py", "other": "meta2"}
        ]],
        "distances": [[0.1, 0.2]]
    }
    return mock_cs


# Tests for PublicKnowledgeQuerier
@pytest.fixture
def mock_upstash_service(mocker):
    """Fixture for a mocked UpstashService."""
    mock_us = MagicMock(spec=UpstashService)
    # Mimic the structure of results from UpstashService.query
    mock_us.query = mocker.AsyncMock(return_value=[
        MagicMock(id="pub_doc1", metadata={"source": "web"}, data="public doc1 content"),
        MagicMock(id="pub_doc2", metadata={"source": "web"}, data="public doc2 content"),
    ])
    return mock_us


# Tests for CurationTriggerProcessor
from cortex.pipelines.curation import CurationProcessor


# Tests for InsightSynthesizer
@pytest.fixture
def insight_synthesizer(mock_llm_service, mock_prompt_manager, mocker):
    """Fixture for InsightSynthesizer with mocked dependencies."""
    # Patch PromptManager at the module level before instantiating InsightSynthesizer
    mocker.patch('cortex.pipelines.synthesis.PromptManager', return_value=mock_prompt_manager)
    return InsightSynthesizer(mock_llm_service)

@pytest.mark.asyncio
async def test_insight_synthesizer_success(insight_synthesizer, mock_llm_service, mock_prompt_manager, mocker):
    """Test successful insight synthesis."""
    data = {
        "private_knowledge": {
            "private_results": {"docs": ["private doc 1"]},
            "traversed_knowledge": ["traversed doc 1"]
        },
        "public_knowledge": {
            "public_results": [MagicMock(data="public doc 1")],
            "augmented_knowledge": "augmented data"
        }
    }
    context = {}
    
    # Set the return value for the synthesis prompt specifically for this test
    mock_prompt_manager.render.return_value = "synthesis prompt content"
    
    # Explicitly mock the generate method of the llm_service within the insight_synthesizer instance
    mocker.patch.object(insight_synthesizer.llm_service, 'generate', return_value="Synthesized Insight")

    result = await insight_synthesizer.process(data, context)
    
    mock_prompt_manager.render.assert_called_once_with(
        "insight_synthesis.jinja2",
        private_results=data["private_knowledge"]["private_results"],
        traversed_knowledge=data["private_knowledge"]["traversed_knowledge"],
        public_results=data["public_knowledge"]["public_results"],
        augmented_knowledge=data["public_knowledge"]["augmented_knowledge"]
    )
    # The assertion now checks the patched object's call
    insight_synthesizer.llm_service.generate.assert_called_once_with(
        "synthesis prompt content",
        model="gemini-pro-test"
    )
    assert "final_insight" in result
    assert result["final_insight"] == "Synthesized Insight"

# Tests for RunPrivatePipeline
from cortex.pipelines.synthesis import RunPrivatePipeline, PrivateKnowledgeQuerier, GraphTraversalProcessor
from cortex.pipelines.pipelines import Pipeline

@pytest.fixture
def run_private_pipeline_instance(mocker, mock_chroma_service, mock_settings):
    """Fixture for RunPrivatePipeline with mocked dependencies."""
    # Patch the *classes* that RunPrivatePipeline instantiates internally
    mocker.patch('cortex.pipelines.synthesis.PrivateKnowledgeQuerier')
    mocker.patch('cortex.pipelines.synthesis.GraphTraversalProcessor')

    # Create a mock Pipeline with an AsyncMock execute method
    mock_pipeline_instance = MagicMock(spec=Pipeline)
    mock_pipeline_instance.execute = AsyncMock(return_value={"private_results": "combined_private_results"})
    mocker.patch('cortex.pipelines.synthesis.Pipeline', return_value=mock_pipeline_instance)

    return RunPrivatePipeline(mock_chroma_service, mock_settings)

@pytest.mark.asyncio
async def test_run_private_pipeline_process_success(run_private_pipeline_instance):
    data = "input data"
    context = {"key": "value"}

    result = await run_private_pipeline_instance.process(data, context)

    # Assert that the execute method of the internal pipeline was called
    run_private_pipeline_instance.pipeline.execute.assert_called_once_with(data, context)

    assert result == {"private_knowledge": {"private_results": "combined_private_results"}}

# Tests for RunPublicPipeline
from cortex.pipelines.synthesis import RunPublicPipeline

@pytest.fixture
def run_public_pipeline_instance(mocker, mock_upstash_service, mock_llm_service):
    """Fixture for RunPublicPipeline with mocked dependencies."""
    # Patch the *classes* that RunPublicPipeline instantiates
    mocker.patch('cortex.pipelines.synthesis.PublicKnowledgeQuerier')
    mocker.patch('cortex.pipelines.synthesis.KnowledgeGatewayProcessor')
    mocker.patch('cortex.pipelines.synthesis.CurationTriggerProcessor')

    # Create a mock Pipeline with an AsyncMock execute method
    mock_pipeline_instance = MagicMock(spec=Pipeline)
    mock_pipeline_instance.execute = AsyncMock(return_value={"public_results": "combined_public_results"})
    mocker.patch('cortex.pipelines.synthesis.Pipeline', return_value=mock_pipeline_instance)

    return RunPublicPipeline(mock_upstash_service, mock_llm_service)

@pytest.mark.asyncio
async def test_run_public_pipeline_process_success(run_public_pipeline_instance):
    data = "public input data"
    context = {"pub_key": "pub_value"}

    result = await run_public_pipeline_instance.process(data, context)

    # Assert that the execute method of the internal pipeline was called
    run_public_pipeline_instance.pipeline.execute.assert_called_once_with(data, context)

    assert result == {"public_knowledge": {"public_results": "combined_public_results"}}
