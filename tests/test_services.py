import pytest
from unittest.mock import MagicMock, patch
from cortex.services.llmservice import LLMService
from cortex.exceptions import ServiceError
import requests

@pytest.fixture
def llm_service(mocker):
    """Fixture to provide an instance of LLMService with mocked Gemini client."""
    # Mock the Google GenAI client initialization to avoid API key requirement
    mocker.patch('google.genai.Client')
    return LLMService()

def test_generate_with_ollama_success(llm_service, mocker):
    """Test successful generation with Ollama."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"response": "  Ollama response.  "}
    mocker.patch('requests.post', return_value=mock_response)

    prompt = "Test prompt for Ollama"
    result = llm_service._generate_with_ollama(prompt, "test-model")

    assert result == "Ollama response."
    requests.post.assert_called_once()

def test_generate_with_ollama_api_error(llm_service, mocker):
    """Test handling of API error from Ollama."""
    mocker.patch('requests.post', side_effect=requests.RequestException("API is down"))

    with pytest.raises(ServiceError, match="Error communicating with local LLM API: API is down"):
        llm_service._generate_with_ollama("prompt", "test-model")

def test_generate_with_gemini_success(llm_service, mocker):
    """Test successful generation with Gemini."""
    # Mock the entire genai client chain
    mock_gemini_client = MagicMock()
    mock_response = MagicMock()
    mock_part = MagicMock()
    mock_part.text = "Gemini response."
    mock_response.parts = [mock_part]
    mock_gemini_client.models.generate_content.return_value = mock_response

    # Since LLMService initializes the client in __init__, we need to patch it on the instance
    mocker.patch.object(llm_service, '_gemini_client', mock_gemini_client)

    prompt = "Test prompt for Gemini"
    result = llm_service._generate_with_gemini(prompt, "gemini-pro")

    assert result == "Gemini response."
    mock_gemini_client.models.generate_content.assert_called_once_with(
        model="gemini-pro",
        contents=prompt
    )

def test_generate_with_gemini_api_error(llm_service, mocker):
    """Test handling of API error from Gemini."""
    mock_gemini_client = MagicMock()
    mock_gemini_client.models.generate_content.side_effect = Exception("Invalid API key")
    mocker.patch.object(llm_service, '_gemini_client', mock_gemini_client)

    with pytest.raises(ServiceError, match="Error communicating with Gemini API: Invalid API key"):
        llm_service._generate_with_gemini("prompt", "gemini-pro")

def test_generate_selects_ollama(llm_service, mocker):
    """Test that the main generate function correctly calls the ollama method."""
    # We mock the internal method to verify it's called
    mock_ollama = mocker.patch.object(llm_service, '_generate_with_ollama', return_value="ollama")
    
    llm_service.generate("prompt", "llama3")

    mock_ollama.assert_called_once_with("prompt", "llama3")

def test_generate_selects_gemini(llm_service, mocker):
    """Test that the main generate function correctly calls the gemini method."""
    mock_gemini = mocker.patch.object(llm_service, '_generate_with_gemini', return_value="gemini")
    
    llm_service.generate("prompt", "gemini-pro")

    mock_gemini.assert_called_once_with("prompt", "gemini-pro")

def test_generate_commit_summary(llm_service, mocker):
    """Test the commit summary generation prompt and flow."""
    mock_generate = mocker.patch.object(llm_service, 'generate')
    
    llm_service.generate_commit_summary("feat: new thing", "diff --git a/file.py b/file.py")

    # Check that the generate method was called, we don't need to be super specific about the prompt content here,
    # just that it was called. More specific prompt tests could be added if needed.
    mock_generate.assert_called_once()
    assert "feat: new thing" in mock_generate.call_args[0][0]
    assert "diff --git" in mock_generate.call_args[0][0]
from cortex.services.chroma_service import ChromaService, OllamaEmbeddingHelper

# Tests for OllamaEmbeddingHelper
def test_get_embedding_success(mocker):
    """Test successful embedding generation."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {"embeddings": [[0.1, 0.2, 0.3]]}
    mocker.patch('requests.post', return_value=mock_response)
    
    helper = OllamaEmbeddingHelper()
    embedding = helper.get_embedding("some text")
    
    assert embedding == [0.1, 0.2, 0.3]
    requests.post.assert_called_once()

def test_get_embedding_api_error(mocker):
    """Test handling of API error during embedding generation."""
    mocker.patch('requests.post', side_effect=requests.RequestException("Embedding API is down"))
    
    helper = OllamaEmbeddingHelper()
    
    with pytest.raises(ServiceError, match="Failed to get embedding from Ollama: Embedding API is down"):
        helper.get_embedding("some text")

# Tests for ChromaService
@pytest.fixture
def chroma_service(mocker):
    """Fixture to provide a mocked instance of ChromaService."""
    # Mock the chromadb client so we don't interact with the real database
    mocker.patch('chromadb.PersistentClient')
    service = ChromaService()
    # Further mock the collection object that is created in __init__
    service.collection = MagicMock()
    return service

def test_add_document_success(chroma_service, mocker):
    """Test successfully adding a document to ChromaDB."""
    mock_embedding = [0.4, 0.5, 0.6]
    # Mock the embedding helper's method within the service instance
    mocker.patch.object(chroma_service.embedding_helper, 'get_embedding', return_value=mock_embedding)
    
    doc_id = "test_doc_1"
    content = "This is a test document."
    metadata = {"source": "test"}
    
    chroma_service.add_document(doc_id, content, metadata)
    
    chroma_service.embedding_helper.get_embedding.assert_called_once_with(content)
    chroma_service.collection.add.assert_called_once_with(
        ids=[doc_id],
        embeddings=[mock_embedding],
        documents=[content],
        metadatas=[metadata]
    )

def test_add_document_chroma_error(chroma_service, mocker):
    """Test handling of an error when adding a document to ChromaDB."""
    mocker.patch.object(chroma_service.embedding_helper, 'get_embedding', return_value=[0.1, 0.2])
    chroma_service.collection.add.side_effect = Exception("ChromaDB unavailable")
    
    with pytest.raises(ServiceError, match="Failed to add document to ChromaDB: ChromaDB unavailable"):
        chroma_service.add_document("id", "content", {})

def test_query_success(chroma_service, mocker):
    """Test a successful query to ChromaDB."""
    query_embedding = [0.7, 0.8, 0.9]
    mock_results = {"documents": [["doc1"]], "metadatas": [[{"source": "test"}]]}
    
    mocker.patch.object(chroma_service.embedding_helper, 'get_embedding', return_value=query_embedding)
    chroma_service.collection.query.return_value = mock_results
    
    query_text = "find similar documents"
    results = chroma_service.query(query_text, n_results=1)
    
    assert results == mock_results
    chroma_service.embedding_helper.get_embedding.assert_called_once_with(query_text)
    chroma_service.collection.query.assert_called_once_with(
        query_embeddings=[query_embedding],
        n_results=1,
        include=["documents", "metadatas"]
    )
import yaml
from datetime import datetime
from cortex.services.knowledge_graph_service import KnowledgeGraphService
from cortex.models.insights import Insight
from cortex.models.events import GitCommitEvent, CodeChangeEvent

# Tests for KnowledgeGraphService
@pytest.fixture
def kg_service(tmp_path):
    """Fixture to provide an instance of KnowledgeGraphService using a temporary directory."""
    return KnowledgeGraphService(base_path=str(tmp_path))

@pytest.fixture
def sample_commit_insight():
    """Fixture for a sample insight from a GitCommitEvent."""
    commit_event = GitCommitEvent(
        repo_name="test-repo",
        branch_name="main",
        commit_hash="abcdef123456",
        message="feat: initial commit",
        timestamp=datetime(2023, 1, 1, 12, 0, 0)
    )
    return Insight(
        insight_id="insight-commit-1",
        summary="Initial feature implementation.",
        content_for_embedding="Initial feature implementation.",
        source_event_type="git_commit",
        source_event=commit_event,
        timestamp=datetime(2023, 1, 1, 12, 0, 0),
        patterns=["Refactoring"],
        metadata={"repo_name": "test-repo"}
    )

@pytest.fixture
def sample_code_change_insight():
    """Fixture for a sample insight from a CodeChangeEvent."""
    change_event = CodeChangeEvent(
        file_path="/path/to/my/file.py",
        change_type="modified",
        content="new file content"
    )
    return Insight(
        insight_id="insight-code-change-1",
        summary="Refactored the file.",
        content_for_embedding="Refactored the file.",
        source_event_type="code_change",
        source_event=change_event,
        timestamp=datetime(2023, 1, 1, 13, 0, 0),
        patterns=["Refactoring"],
        metadata={}
    )

def test_kg_creates_directories(kg_service, tmp_path):
    """Test that the service creates the necessary base directories."""
    assert (tmp_path / "insights").is_dir()
    assert (tmp_path / "repositories").is_dir()

def test_create_insight_node_for_commit(kg_service, sample_commit_insight, tmp_path):
    """Test creating an insight node for a git commit."""
    kg_service._create_insight_node(sample_commit_insight)
    
    expected_filename = "git.commit.abcdef123456.md"
    insight_file = tmp_path / "insights" / expected_filename
    
    assert insight_file.exists()
    
    with open(insight_file, "r") as f:
        content = f.read()
        # Fast check for content
        assert "insight-commit-1" in content
        assert "parent_nodes" in content
        assert "[[../repositories/test-repo.md]]" in content
        assert "# Insight: Initial feature implementation." in content

def test_update_index_node(kg_service, tmp_path):
    """Test creating and appending to an index node."""
    index_file = tmp_path / "repositories" / "my-repo.md"
    link_to_add = tmp_path / "insights" / "some-insight.md"
    
    # First update (creates the file)
    kg_service._update_index_node(index_file, link_to_add)
    
    assert index_file.exists()
    with open(index_file, "r") as f:
        content = f.read()
        assert "## Related Insights" in content
        assert "- [[../insights/some-insight.md]]" in content
        
    # Second update (appends to the file)
    link_to_add_2 = tmp_path / "insights" / "another-insight.md"
    kg_service._update_index_node(index_file, link_to_add_2)
    
    with open(index_file, "r") as f:
        content = f.read()
        assert content.count("- [[") == 2
        assert "- [[../insights/another-insight.md]]" in content

def test_process_insight_for_commit(kg_service, sample_commit_insight, tmp_path):
    """Test the end-to-end processing of a commit insight."""
    kg_service.process_insight(sample_commit_insight)
    
    insight_file = tmp_path / "insights" / "git.commit.abcdef123456.md"
    repo_file = tmp_path / "repositories" / "test-repo.md"
    
    assert insight_file.exists()
    assert repo_file.exists()
    
    with open(repo_file, "r") as f:
        content = f.read()
        assert "[[../insights/git.commit.abcdef123456.md]]" in content
        
def test_process_insight_for_code_change(kg_service, sample_code_change_insight, tmp_path):
    """Test the end-to-end processing of a code change insight (should not update repo index)."""
    kg_service.process_insight(sample_code_change_insight)
    
    # Filename contains a hash of the path and a timestamp
    expected_filename_prefix = "code.change."
    insight_dir = tmp_path / "insights"
    matching_files = list(insight_dir.glob(f"{expected_filename_prefix}*.md"))
    
    assert len(matching_files) == 1
    
    # Check that no repo file was created for a code change event without repo metadata
    repo_file = tmp_path / "repositories" / "None.md" # What it might try to create
    assert not repo_file.exists()

# Tests for UpstashService
from cortex.services.upstash_service import UpstashService
from upstash_vector.types import Data

@pytest.fixture
def upstash_service(mocker):
    """Fixture to provide a mocked instance of UpstashService."""
    mock_index = MagicMock()
    mock_index.upsert = mocker.AsyncMock()
    mock_index.query = mocker.AsyncMock()
    mocker.patch('cortex.services.upstash_service.AsyncIndex', return_value=mock_index)
    service = UpstashService()
    return service

@pytest.mark.asyncio
async def test_add_document_success(upstash_service):
    """Test successfully adding a document to Upstash."""
    doc_id = "upstash_doc_1"
    content = "Upstash test content."
    metadata = {"source": "upstash"}
    
    await upstash_service.add_document(doc_id, content, metadata)
    
    upstash_service.index.upsert.assert_called_once_with(
        vectors=[
            Data(id=doc_id, metadata=metadata, data=content)
        ]
    )

@pytest.mark.asyncio
async def test_add_document_error(upstash_service):
    """Test handling of an error when adding a document to Upstash."""
    upstash_service.index.upsert.side_effect = Exception("Upstash is down")
    
    doc_id = "upstash_doc_error"
    content = "Error content."
    metadata = {"source": "error"}

    # We don't expect a ServiceError here, as the current implementation only logs the error.
    # If the requirement changes to raise a ServiceError, this test would need to be updated.
    await upstash_service.add_document(doc_id, content, metadata)
    upstash_service.index.upsert.assert_called_once()
    # Further assertions could be added to check logging output if needed.

@pytest.mark.asyncio
async def test_query_success(upstash_service, mocker):
    """Test a successful query to Upstash."""
    mock_results = [MagicMock(id="res1", metadata={"s": "u"}, data="res data")]
    
    # The AsyncMock for query is already set in the fixture, just set its return value
    upstash_service.index.query.return_value = mock_results

    query_text = "query upstash"
    results = await upstash_service.query(query_text, n_results=1)
    
    assert results == mock_results
    upstash_service.index.query.assert_called_once_with(
        data=query_text,
        top_k=1,
        include_metadata=True
    )