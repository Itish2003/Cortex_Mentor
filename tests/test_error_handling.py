import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from cortex.pipelines.delivery import AudioDeliveryProcessor
from cortex.exceptions import ProcessorError, ServiceError
from google.cloud import texttospeech
import asyncio
from cortex.services.knowledge_graph_service import KnowledgeGraphService
from cortex.models.insights import Insight
from cortex.models.events import GitCommitEvent
from datetime import datetime
import os
import requests
from cortex.services.chroma_service import ChromaService, OllamaEmbeddingHelper

# Mock the Redis client for testing
@pytest.fixture
def mock_redis():
    return AsyncMock()

# Mock the TextToSpeechClient for testing
@pytest.fixture
def mock_tts_client():
    with patch('cortex.pipelines.delivery.texttospeech.TextToSpeechClient') as MockTTS:
        instance = MockTTS.return_value
        yield instance

@pytest.mark.asyncio
async def test_audio_delivery_processor_synthesize_speech_failure(mock_redis, mock_tts_client):
    processor = AudioDeliveryProcessor(redis=mock_redis)
    data = {"final_insight": "Test insight"}
    
    # Simulate synthesize_speech raising an exception
    mock_tts_client.synthesize_speech.side_effect = Exception("TTS error")

    with pytest.raises(ProcessorError, match="Error during audio generation or publishing"):
        await processor.process(data, {})

@pytest.mark.asyncio
async def test_audio_delivery_processor_publish_failure(mock_redis, mock_tts_client):
    processor = AudioDeliveryProcessor(redis=mock_redis)
    data = {"final_insight": "Test insight"}
    
    # Simulate successful synthesize_speech
    mock_tts_client.synthesize_speech.return_value = MagicMock(audio_content=b"audio_data")

    # Simulate redis.publish raising an exception
    mock_redis.publish.side_effect = Exception("Redis publish error")

    with pytest.raises(ProcessorError, match="Error during audio generation or publishing"):
        await processor.process(data, {})

# Mock Insight for testing
@pytest.fixture
def mock_insight():
    return Insight(
        insight_id="test_insight",
        source_event_type="git_commit",
        timestamp=datetime.now(),
        summary="Test summary",
        patterns=[],
        metadata={},
        content_for_embedding="Test content",
        source_event=GitCommitEvent(
            event_type="git_commit",
            repo_name="test-repo",
            commit_hash="1234567890",
            author_name="Test Author",
            author_email="test@example.com",
            message="Test commit message",
            diff="",
            branch_name="main",
            timestamp=datetime.now()
        )
    )

@patch("pathlib.Path.mkdir")
@patch("builtins.open")
def test_knowledge_graph_service_create_insight_node_failure(mock_open, mock_mkdir, mock_insight):
    kg_service = KnowledgeGraphService(base_path="/fake/path")
    mock_open.side_effect = IOError("File system is full")

    with pytest.raises(ServiceError, match="Error creating insight node"):
        kg_service._create_insight_node(mock_insight)

@patch("pathlib.Path.mkdir")
@patch("builtins.open")
def test_knowledge_graph_service_update_index_node_failure(mock_open, mock_mkdir):
    kg_service = KnowledgeGraphService(base_path="/fake/path")
    mock_open.side_effect = IOError("Permission denied")

    with pytest.raises(ServiceError, match="Error updating index node"):
        kg_service._update_index_node(
            index_file=kg_service.base_path / "index.md",
            link_to_add=kg_service.base_path / "insights" / "link.md"
        )

@patch('requests.post')
def test_ollama_embedding_helper_get_embedding_failure(mock_post):
    mock_post.side_effect = requests.exceptions.RequestException("Network error")
    
    helper = OllamaEmbeddingHelper()
    
    with pytest.raises(ServiceError, match="Failed to get embedding from Ollama"):
        helper.get_embedding("some text")

@patch('cortex.services.chroma_service.OllamaEmbeddingHelper.get_embedding')
@patch('chromadb.Collection.add')
def test_chroma_service_add_document_failure(mock_add, mock_get_embedding):
    mock_get_embedding.return_value = [0.1, 0.2, 0.3]
    mock_add.side_effect = Exception("ChromaDB error")
    
    # We need to patch the constructor of ChromaService to avoid it trying to connect to a real DB
    with patch.object(ChromaService, '__init__', lambda self: None):
        service = ChromaService()
        service.embedding_helper = OllamaEmbeddingHelper() # we need to re-add the helper
        service.collection = MagicMock()
        service.collection.add.side_effect = Exception("ChromaDB error")

        with pytest.raises(ServiceError, match="Failed to add document to ChromaDB"):
            service.add_document("doc1", "some content", {})