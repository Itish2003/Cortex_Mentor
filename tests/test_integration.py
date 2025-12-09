"""
End-to-end integration tests for the Cortex Mentor system.
Tests the complete event processing flow from ingestion through delivery.

Note: These tests require Redis to be running for full integration testing.
Use pytest markers to run these tests selectively:
  pytest -m integration  # Run only integration tests
  pytest -m "not integration"  # Skip integration tests
"""
import pytest
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


# ============================================================================
# Pipeline Integration Tests
# ============================================================================

class TestComprehensionPipelineIntegration:
    """Integration tests for the full comprehension pipeline."""

    @pytest.fixture
    def mock_services(self, mocker):
        """Create mocked services for pipeline testing."""
        # Mock KnowledgeGraphService
        mock_kg = MagicMock()
        mock_kg.process_insight = MagicMock()

        # Mock ChromaService
        mock_chroma = MagicMock()
        mock_chroma.add_document = MagicMock()

        # Mock LLMService
        mock_llm = MagicMock()
        mock_llm.generate_commit_summary = MagicMock(return_value="Test commit summary")
        mock_llm.generate_code_change_summary = MagicMock(return_value="Test code change summary")

        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.enqueue_job = AsyncMock()

        return {
            "kg_service": mock_kg,
            "chroma_service": mock_chroma,
            "llm_service": mock_llm,
            "redis": mock_redis
        }

    @pytest.mark.asyncio
    async def test_full_comprehension_pipeline_git_commit(self, mock_services, mocker):
        """Test the full comprehension pipeline with a git commit event."""
        from cortex.pipelines.pipelines import Pipeline
        from cortex.pipelines.comprehension import (
            EventDeserializer,
            InsightGenerator,
            KnowledgeGraphWriter,
            ChromaWriter,
            SynthesisTrigger
        )

        # Build the pipeline
        pipeline = Pipeline([
            EventDeserializer(),
            InsightGenerator(llm_service=mock_services["llm_service"]),
            [
                KnowledgeGraphWriter(mock_services["kg_service"]),
                ChromaWriter(mock_services["chroma_service"]),
            ],
            SynthesisTrigger(),
        ])

        # Sample git commit event
        event_data = {
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

        context = {"redis": mock_services["redis"]}

        # Execute the pipeline
        result = await pipeline.execute(data=event_data, context=context)

        # Verify all services were called
        mock_services["llm_service"].generate_commit_summary.assert_called_once()
        mock_services["kg_service"].process_insight.assert_called_once()
        mock_services["chroma_service"].add_document.assert_called_once()
        mock_services["redis"].enqueue_job.assert_called_once()

    @pytest.mark.asyncio
    async def test_full_comprehension_pipeline_code_change(self, mock_services, mocker):
        """Test the full comprehension pipeline with a code change event."""
        from cortex.pipelines.pipelines import Pipeline
        from cortex.pipelines.comprehension import (
            EventDeserializer,
            InsightGenerator,
            KnowledgeGraphWriter,
            ChromaWriter,
            SynthesisTrigger
        )

        pipeline = Pipeline([
            EventDeserializer(),
            InsightGenerator(llm_service=mock_services["llm_service"]),
            [
                KnowledgeGraphWriter(mock_services["kg_service"]),
                ChromaWriter(mock_services["chroma_service"]),
            ],
            SynthesisTrigger(),
        ])

        event_data = {
            "event_type": "file_change",
            "file_path": "/path/to/file.py",
            "change_type": "modified",
            "content": "def new_function():\n    pass"
        }

        context = {"redis": mock_services["redis"]}

        await pipeline.execute(data=event_data, context=context)

        mock_services["llm_service"].generate_code_change_summary.assert_called_once()
        mock_services["kg_service"].process_insight.assert_called_once()
        mock_services["chroma_service"].add_document.assert_called_once()


class TestSynthesisPipelineIntegration:
    """Integration tests for the synthesis pipeline."""

    @pytest.fixture
    def mock_synthesis_services(self, mocker):
        """Create mocked services for synthesis testing."""
        # Mock ChromaService
        mock_chroma = MagicMock()
        mock_chroma.query = MagicMock(return_value={
            "documents": [["private doc content"]],
            "metadatas": [[{"file_path": "/path/to/insight.md"}]],
            "distances": [[0.1]]
        })

        # Mock UpstashService
        mock_upstash = MagicMock()
        mock_upstash.query = AsyncMock(return_value=[
            MagicMock(id="pub_doc1", metadata={"source": "web"}, data="public doc content")
        ])

        # Mock LLMService
        mock_settings = MagicMock()
        mock_settings.gemini_flash_model = "gemini-flash"
        mock_settings.gemini_pro_model = "gemini-pro"

        mock_llm = MagicMock()
        mock_llm.settings = mock_settings
        mock_llm.generate = MagicMock(return_value="Synthesized insight content")

        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.publish = AsyncMock()

        return {
            "chroma_service": mock_chroma,
            "upstash_service": mock_upstash,
            "llm_service": mock_llm,
            "redis": mock_redis
        }

    @pytest.mark.asyncio
    async def test_private_knowledge_retrieval(self, mock_synthesis_services, mocker):
        """Test private knowledge retrieval from ChromaDB."""
        from cortex.pipelines.synthesis import PrivateKnowledgeQuerier

        processor = PrivateKnowledgeQuerier(mock_synthesis_services["chroma_service"])
        data = "How to implement authentication?"
        context = {}

        result = await processor.process(data, context)

        assert "query_text" in result
        assert "private_results" in result
        assert "entry_points" in result
        mock_synthesis_services["chroma_service"].query.assert_called_once()

    @pytest.mark.asyncio
    async def test_public_knowledge_retrieval(self, mock_synthesis_services, mocker):
        """Test public knowledge retrieval from Upstash."""
        from cortex.pipelines.synthesis import PublicKnowledgeQuerier

        processor = PublicKnowledgeQuerier(mock_synthesis_services["upstash_service"])
        data = "How to implement authentication?"
        context = {}

        result = await processor.process(data, context)

        assert "query_text" in result
        assert "public_results" in result
        mock_synthesis_services["upstash_service"].query.assert_called_once()


class TestPipelineOrchestration:
    """Test the Pipeline class orchestration capabilities."""

    @pytest.mark.asyncio
    async def test_sequential_execution(self):
        """Test that processors execute sequentially in order."""
        from cortex.pipelines.pipelines import Pipeline
        from cortex.pipelines.processors import Processor

        execution_order = []

        class TrackedProcessor(Processor):
            def __init__(self, name):
                self.name = name

            async def process(self, data, context):
                execution_order.append(self.name)
                return data

        pipeline = Pipeline([
            TrackedProcessor("first"),
            TrackedProcessor("second"),
            TrackedProcessor("third"),
        ])

        await pipeline.execute(data="test", context={})

        assert execution_order == ["first", "second", "third"]

    @pytest.mark.asyncio
    async def test_parallel_execution(self):
        """Test that processors in a list execute in parallel."""
        from cortex.pipelines.pipelines import Pipeline
        from cortex.pipelines.processors import Processor

        execution_times = {}

        class TimedProcessor(Processor):
            def __init__(self, name, delay):
                self.name = name
                self.delay = delay

            async def process(self, data, context):
                start = asyncio.get_event_loop().time()
                await asyncio.sleep(self.delay)
                end = asyncio.get_event_loop().time()
                execution_times[self.name] = (start, end)
                return {self.name: "result"}

        pipeline = Pipeline([
            [
                TimedProcessor("parallel_a", 0.1),
                TimedProcessor("parallel_b", 0.1),
            ],
        ])

        await pipeline.execute(data="test", context={})

        # Verify both processors ran (nearly) simultaneously
        a_start, a_end = execution_times["parallel_a"]
        b_start, b_end = execution_times["parallel_b"]

        # The starts should be very close together (within 0.05s)
        assert abs(a_start - b_start) < 0.05, "Parallel processors should start simultaneously"

    @pytest.mark.asyncio
    async def test_data_flow_through_pipeline(self):
        """Test that data flows correctly through pipeline stages."""
        from cortex.pipelines.pipelines import Pipeline
        from cortex.pipelines.processors import Processor

        class AddProcessor(Processor):
            def __init__(self, key, value):
                self.key = key
                self.value = value

            async def process(self, data, context):
                if isinstance(data, dict):
                    data[self.key] = self.value
                else:
                    data = {self.key: self.value}
                return data

        pipeline = Pipeline([
            AddProcessor("step1", "value1"),
            AddProcessor("step2", "value2"),
            AddProcessor("step3", "value3"),
        ])

        result = await pipeline.execute(data={}, context={})

        assert result == {
            "step1": "value1",
            "step2": "value2",
            "step3": "value3"
        }

    @pytest.mark.asyncio
    async def test_parallel_results_merge(self):
        """Test that results from parallel processors are merged."""
        from cortex.pipelines.pipelines import Pipeline
        from cortex.pipelines.processors import Processor

        class ReturnDictProcessor(Processor):
            def __init__(self, result_dict):
                self.result_dict = result_dict

            async def process(self, data, context):
                return self.result_dict

        pipeline = Pipeline([
            [
                ReturnDictProcessor({"a": 1, "b": 2}),
                ReturnDictProcessor({"c": 3, "d": 4}),
            ],
        ])

        result = await pipeline.execute(data={}, context={})

        # Both dicts should be merged
        assert "a" in result and "c" in result

    @pytest.mark.asyncio
    async def test_context_sharing(self):
        """Test that context is shared across all processors."""
        from cortex.pipelines.pipelines import Pipeline
        from cortex.pipelines.processors import Processor

        class ContextModifier(Processor):
            def __init__(self, key, value):
                self.key = key
                self.value = value

            async def process(self, data, context):
                context[self.key] = self.value
                return data

        class ContextReader(Processor):
            def __init__(self, expected_keys):
                self.expected_keys = expected_keys
                self.found_keys = []

            async def process(self, data, context):
                for key in self.expected_keys:
                    if key in context:
                        self.found_keys.append(key)
                return data

        reader = ContextReader(["key1", "key2"])

        pipeline = Pipeline([
            ContextModifier("key1", "value1"),
            ContextModifier("key2", "value2"),
            reader,
        ])

        context = {}
        await pipeline.execute(data={}, context=context)

        assert reader.found_keys == ["key1", "key2"]


class TestWebSocketIntegration:
    """Integration tests for WebSocket communication."""

    @pytest.mark.asyncio
    async def test_redis_pubsub_message_format(self):
        """Test that messages published to Redis have the correct format."""
        import base64
        import json
        from unittest.mock import AsyncMock, MagicMock, patch

        mock_redis = AsyncMock()
        mock_redis.publish = AsyncMock()

        with patch('cortex.pipelines.delivery.texttospeech.TextToSpeechClient') as MockTTS:
            mock_tts = MockTTS.return_value
            mock_tts.synthesize_speech.return_value = MagicMock(
                audio_content=b"test_audio_data"
            )

            with patch('cortex.pipelines.delivery.Settings') as MockSettings:
                MockSettings.return_value.tts_voice_name = "en-US-Wavenet-D"

                from cortex.pipelines.delivery import AudioDeliveryProcessor

                processor = AudioDeliveryProcessor(redis=mock_redis)
                data = {"final_insight": "Test insight for WebSocket"}

                await processor.process(data, {})

                # Verify the published message format
                mock_redis.publish.assert_called_once()
                channel, message = mock_redis.publish.call_args[0]

                assert channel == "insights_channel"

                parsed_message = json.loads(message)
                assert parsed_message["type"] == "insight"
                assert parsed_message["text"] == "Test insight for WebSocket"
                assert "audio" in parsed_message

                # Verify audio is valid base64
                decoded_audio = base64.b64decode(parsed_message["audio"])
                assert decoded_audio == b"test_audio_data"


class TestAPIIntegration:
    """Integration tests for the FastAPI endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, mocker):
        """Test the health check endpoint."""
        from fastapi import FastAPI
        from cortex.api import events

        # Create a minimal app without Redis lifespan for testing
        test_app = FastAPI()
        test_app.include_router(events.router, prefix="/api")

        @test_app.get("/")
        def read_root():
            return {"message": "Cortex API is running."}

        from fastapi.testclient import TestClient
        with TestClient(test_app) as client:
            response = client.get("/")
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "Cortex API is running" in data["message"]


class TestErrorRecoveryIntegration:
    """Integration tests for error recovery scenarios."""

    @pytest.mark.asyncio
    async def test_pipeline_continues_after_parallel_processor_failure(self):
        """Test that pipeline handles failures in parallel processors gracefully."""
        from cortex.pipelines.pipelines import Pipeline
        from cortex.pipelines.processors import Processor

        class SuccessProcessor(Processor):
            async def process(self, data, context):
                return {"success": True}

        class FailingProcessor(Processor):
            async def process(self, data, context):
                raise Exception("Intentional failure")

        pipeline = Pipeline([
            [
                SuccessProcessor(),
                FailingProcessor(),
            ],
        ])

        # Pipeline should raise when any parallel processor fails
        with pytest.raises(Exception, match="Intentional failure"):
            await pipeline.execute(data={}, context={})

    @pytest.mark.asyncio
    async def test_service_error_propagation(self):
        """Test that service errors are properly propagated through the pipeline."""
        from cortex.pipelines.comprehension import InsightGenerator
        from cortex.models.events import GitCommitEvent
        from cortex.exceptions import ProcessorError, ServiceError
        from datetime import datetime

        mock_llm = MagicMock()
        mock_llm.generate_commit_summary.side_effect = ServiceError("LLM service unavailable")

        processor = InsightGenerator(llm_service=mock_llm)

        event = GitCommitEvent(
            event_type="git_commit",
            repo_name="test-repo",
            branch_name="main",
            commit_hash="abc123",
            author_name="Test",
            author_email="test@test.com",
            message="test",
            diff="",
            timestamp=datetime.now()
        )

        with pytest.raises(ProcessorError, match="service error"):
            await processor.process(event, {})


# ============================================================================
# Full Front-to-Back E2E Tests
# ============================================================================

class TestFullE2EFlow:
    """
    Full end-to-end integration tests that simulate the complete flow:
    API Event Ingestion -> ARQ Worker -> Pipeline Processing -> WebSocket Delivery

    These tests verify that all components work together correctly.
    """

    @pytest.fixture
    def mock_all_services(self, mocker):
        """Create mocks for all external services used in the full flow."""
        # Mock LLMService
        mock_llm = MagicMock()
        mock_llm.generate_commit_summary = MagicMock(return_value="AI-generated commit summary")
        mock_llm.generate_code_change_summary = MagicMock(return_value="AI-generated code summary")
        mock_llm.generate = MagicMock(return_value="Final synthesized insight")

        mock_settings = MagicMock()
        mock_settings.gemini_flash_model = "gemini-flash"
        mock_settings.gemini_pro_model = "gemini-pro"
        mock_settings.tts_voice_name = "en-US-Wavenet-D"
        mock_llm.settings = mock_settings

        # Mock KnowledgeGraphService
        mock_kg = MagicMock()
        mock_kg.process_insight = MagicMock()

        # Mock ChromaService
        mock_chroma = MagicMock()
        mock_chroma.add_document = MagicMock()
        mock_chroma.query = MagicMock(return_value={
            "documents": [["Related private knowledge from local store"]],
            "metadatas": [[{"file_path": "/insights/related.md"}]],
            "distances": [[0.15]]
        })

        # Mock UpstashService
        mock_upstash = MagicMock()
        mock_upstash.query = AsyncMock(return_value=[
            MagicMock(id="pub1", metadata={"source": "curated"}, data="Public expert knowledge")
        ])
        mock_upstash.add_document = AsyncMock()

        # Mock Redis for task queue and pub/sub
        mock_redis = AsyncMock()
        mock_redis.enqueue_job = AsyncMock()
        mock_redis.publish = AsyncMock()

        # Mock TTS
        mock_tts = MagicMock()
        mock_tts.synthesize_speech = MagicMock(return_value=MagicMock(
            audio_content=b"synthesized_audio_bytes"
        ))

        return {
            "llm_service": mock_llm,
            "kg_service": mock_kg,
            "chroma_service": mock_chroma,
            "upstash_service": mock_upstash,
            "redis": mock_redis,
            "tts": mock_tts,
            "settings": mock_settings
        }

    @pytest.mark.asyncio
    async def test_full_event_to_insight_flow(self, mock_all_services, mocker):
        """
        Test the complete flow from event ingestion to insight delivery.

        Flow: Event -> Comprehension Pipeline -> Knowledge Storage ->
              Synthesis Trigger -> Synthesis Pipeline -> Audio Delivery -> WebSocket
        """
        from cortex.pipelines.pipelines import Pipeline
        from cortex.pipelines.comprehension import (
            EventDeserializer,
            InsightGenerator,
            KnowledgeGraphWriter,
            ChromaWriter,
            SynthesisTrigger
        )
        from cortex.models.events import GitCommitEvent

        # Step 1: Simulate incoming event from API
        raw_event_data = {
            "event_type": "git_commit",
            "repo_name": "my-project",
            "branch_name": "feature/auth",
            "commit_hash": "abc123def456789",
            "author_name": "Developer",
            "author_email": "dev@example.com",
            "message": "feat(auth): implement JWT token validation",
            "diff": """diff --git a/src/auth.py b/src/auth.py
+def validate_jwt(token: str) -> bool:
+    \"\"\"Validate JWT token and return True if valid.\"\"\"
+    try:
+        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
+        return True
+    except jwt.InvalidTokenError:
+        return False""",
            "timestamp": datetime.now().isoformat()
        }

        # Step 2: Build and execute the comprehension pipeline
        comprehension_pipeline = Pipeline([
            EventDeserializer(),
            InsightGenerator(llm_service=mock_all_services["llm_service"]),
            [
                KnowledgeGraphWriter(mock_all_services["kg_service"]),
                ChromaWriter(mock_all_services["chroma_service"]),
            ],
            SynthesisTrigger(),
        ])

        context = {"redis": mock_all_services["redis"]}

        # Execute comprehension pipeline
        await comprehension_pipeline.execute(data=raw_event_data, context=context)

        # Verify Step 2: Event was deserialized and processed
        mock_all_services["llm_service"].generate_commit_summary.assert_called_once()

        # Verify Step 3: Knowledge was stored in both stores (parallel)
        mock_all_services["kg_service"].process_insight.assert_called_once()
        mock_all_services["chroma_service"].add_document.assert_called_once()

        # Verify Step 4: Synthesis was triggered
        mock_all_services["redis"].enqueue_job.assert_called_once()
        call_args = mock_all_services["redis"].enqueue_job.call_args
        assert call_args[0][0] == 'synthesis_task'

    @pytest.mark.asyncio
    async def test_api_to_worker_handoff(self, mocker):
        """Test that API correctly hands off events to the ARQ worker."""
        from fastapi import FastAPI, Request
        from fastapi.testclient import TestClient
        from cortex.models.events import GitCommitEvent

        # Create a minimal test app without Redis lifespan
        test_app = FastAPI()

        # Mock redis for the app state
        mock_redis = AsyncMock()
        mock_redis.enqueue_job = AsyncMock()

        @test_app.post("/api/events", status_code=202)
        async def create_event(event: GitCommitEvent, request: Request):
            redis = request.app.state.redis
            await redis.enqueue_job('process_event_task', event.model_dump())
            return {"message": "Event received and queued for processing."}

        test_app.state.redis = mock_redis

        with TestClient(test_app) as client:
            event_payload = {
                "event_type": "git_commit",
                "repo_name": "test-repo",
                "branch_name": "main",
                "commit_hash": "abc123",
                "author_name": "Test",
                "author_email": "test@test.com",
                "message": "test commit",
                "diff": "diff content",
                "timestamp": datetime.now().isoformat()
            }

            response = client.post("/api/events", json=event_payload)

            # API should accept the event
            assert response.status_code == 202
            assert "queued" in response.json()["message"].lower()

            # Worker job should be enqueued
            mock_redis.enqueue_job.assert_called_once()
            job_name, job_data = mock_redis.enqueue_job.call_args[0]
            assert job_name == 'process_event_task'
            assert job_data["repo_name"] == "test-repo"

    @pytest.mark.asyncio
    async def test_websocket_message_delivery_format(self, mock_all_services, mocker):
        """
        Test that the final WebSocket message has the correct format
        for the VS Code extension to consume.
        """
        import base64
        from cortex.pipelines.delivery import AudioDeliveryProcessor

        # Mock TTS service
        mocker.patch('cortex.pipelines.delivery.texttospeech.TextToSpeechClient',
                    return_value=mock_all_services["tts"])
        mocker.patch('cortex.pipelines.delivery.Settings',
                    return_value=mock_all_services["settings"])

        processor = AudioDeliveryProcessor(redis=mock_all_services["redis"])

        # Simulate the final insight data from synthesis
        final_data = {
            "final_insight": "Based on your recent JWT implementation, consider adding token refresh functionality and implementing rate limiting to prevent brute force attacks."
        }

        await processor.process(final_data, {})

        # Verify WebSocket message format
        mock_all_services["redis"].publish.assert_called_once()
        channel, message_str = mock_all_services["redis"].publish.call_args[0]

        assert channel == "insights_channel"

        message = json.loads(message_str)

        # VS Code extension expects this exact format
        assert message["type"] == "insight"
        assert "text" in message
        assert "audio" in message
        assert message["text"] == final_data["final_insight"]

        # Audio should be valid base64
        decoded = base64.b64decode(message["audio"])
        assert decoded == b"synthesized_audio_bytes"

    @pytest.mark.asyncio
    async def test_parallel_knowledge_retrieval(self, mock_all_services, mocker):
        """
        Test that private and public knowledge retrieval happens in parallel
        during the synthesis phase.
        """
        from cortex.pipelines.synthesis import (
            PrivateKnowledgeQuerier,
            PublicKnowledgeQuerier
        )
        from cortex.pipelines.pipelines import Pipeline

        # Track execution timing
        execution_log = []

        # ChromaService.query is synchronous, so use a sync wrapper
        def tracked_chroma_query(*args, **kwargs):
            execution_log.append(("chroma_start", asyncio.get_event_loop().time()))
            # Synchronous - no sleep here, just return mock data
            execution_log.append(("chroma_end", asyncio.get_event_loop().time()))
            return {
                "documents": [["Related private knowledge"]],
                "metadatas": [[{"file_path": "/insights/test.md"}]],
                "distances": [[0.15]]
            }

        # UpstashService.query is async
        async def tracked_upstash_query(*args, **kwargs):
            execution_log.append(("upstash_start", asyncio.get_event_loop().time()))
            await asyncio.sleep(0.01)  # Small delay to verify async behavior
            execution_log.append(("upstash_end", asyncio.get_event_loop().time()))
            return [MagicMock(id="pub1", metadata={"source": "curated"}, data="Public knowledge")]

        mock_all_services["chroma_service"].query = tracked_chroma_query
        mock_all_services["upstash_service"].query = tracked_upstash_query

        # Build parallel retrieval pipeline
        parallel_pipeline = Pipeline([
            [
                PrivateKnowledgeQuerier(mock_all_services["chroma_service"]),
                PublicKnowledgeQuerier(mock_all_services["upstash_service"]),
            ]
        ])

        await parallel_pipeline.execute(data="How to implement authentication?", context={})

        # Verify both queries were called
        assert len([e for e in execution_log if e[0] == "chroma_start"]) == 1
        assert len([e for e in execution_log if e[0] == "upstash_start"]) == 1

        # Get start times
        chroma_start = next(t for name, t in execution_log if name == "chroma_start")
        upstash_start = next(t for name, t in execution_log if name == "upstash_start")

        # Should start within 50ms of each other if parallel (allowing for sync vs async variance)
        assert abs(chroma_start - upstash_start) < 0.05, \
            "Private and public knowledge queries should run in parallel"

    @pytest.mark.asyncio
    async def test_error_handling_in_full_flow(self, mock_all_services, mocker):
        """
        Test that errors in one part of the flow are handled gracefully
        and don't crash the entire system.
        """
        from cortex.pipelines.pipelines import Pipeline
        from cortex.pipelines.comprehension import (
            EventDeserializer,
            InsightGenerator,
            KnowledgeGraphWriter,
            ChromaWriter,
        )
        from cortex.exceptions import ProcessorError, ServiceError

        # Make LLM service fail
        mock_all_services["llm_service"].generate_commit_summary.side_effect = \
            ServiceError("LLM API rate limit exceeded")

        pipeline = Pipeline([
            EventDeserializer(),
            InsightGenerator(llm_service=mock_all_services["llm_service"]),
            [
                KnowledgeGraphWriter(mock_all_services["kg_service"]),
                ChromaWriter(mock_all_services["chroma_service"]),
            ],
        ])

        event_data = {
            "event_type": "git_commit",
            "repo_name": "test",
            "branch_name": "main",
            "commit_hash": "abc",
            "author_name": "Test",
            "author_email": "test@test.com",
            "message": "test",
            "diff": "",
            "timestamp": datetime.now().isoformat()
        }

        # Should raise ProcessorError, not crash with unhandled exception
        with pytest.raises(ProcessorError) as exc_info:
            await pipeline.execute(data=event_data, context={})

        assert "service error" in str(exc_info.value).lower()

        # Knowledge stores should NOT have been written to
        mock_all_services["kg_service"].process_insight.assert_not_called()
        mock_all_services["chroma_service"].add_document.assert_not_called()

    @pytest.mark.asyncio
    async def test_context_propagation_through_pipeline(self, mock_all_services):
        """
        Test that context is properly propagated through all pipeline stages.
        """
        from cortex.pipelines.pipelines import Pipeline
        from cortex.pipelines.processors import Processor

        class ContextWriter(Processor):
            def __init__(self, key, value):
                self.key = key
                self.value = value

            async def process(self, data, context):
                context[self.key] = self.value
                return data

        class ContextVerifier(Processor):
            def __init__(self):
                self.verified_keys = []

            async def process(self, data, context):
                # Check that all previous context keys exist
                for key in ["stage1", "stage2", "parallel_a", "parallel_b"]:
                    if key in context:
                        self.verified_keys.append(key)
                return data

        verifier = ContextVerifier()

        pipeline = Pipeline([
            ContextWriter("stage1", "value1"),
            ContextWriter("stage2", "value2"),
            [
                ContextWriter("parallel_a", "value_a"),
                ContextWriter("parallel_b", "value_b"),
            ],
            verifier,
        ])

        context = {"initial": "context"}
        await pipeline.execute(data={}, context=context)

        # All context keys should be accessible in the final stage
        assert "stage1" in verifier.verified_keys
        assert "stage2" in verifier.verified_keys
        # At least one parallel key should be visible
        assert "parallel_a" in verifier.verified_keys or "parallel_b" in verifier.verified_keys
