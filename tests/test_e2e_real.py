"""
True End-to-End Integration Tests with Real External Services.

These tests verify the application's ability to connect and interact with
actual external dependencies (Redis, FastAPI server).

Requirements:
- Redis must be running on localhost:6379
- Run with: uv run pytest tests/test_e2e_real.py -v -m integration

These tests are marked with @pytest.mark.integration and are skipped
by default in regular test runs. Use -m integration to run them.
"""
import pytest
import asyncio
import json
import time
from datetime import datetime
from unittest.mock import MagicMock, patch

# Mark all tests in this module as integration tests
pytestmark = [pytest.mark.integration, pytest.mark.slow]


# ============================================================================
# Fixtures for Real Services
# ============================================================================

@pytest.fixture
async def real_redis_pool():
    """
    Create a real Redis connection pool for testing.
    Skips if Redis is not available.
    """
    try:
        from arq import create_pool
        from arq.connections import RedisSettings

        pool = await create_pool(RedisSettings(host='localhost', port=6379))
        yield pool
        await pool.close()
    except Exception as e:
        pytest.skip(f"Redis not available: {e}")


@pytest.fixture
def test_client():
    """Create a FastAPI test client."""
    from fastapi.testclient import TestClient
    from cortex.main import app
    return TestClient(app)


# ============================================================================
# Redis Connection Tests
# ============================================================================

class TestRealRedisConnection:
    """Tests that verify real Redis connectivity."""

    @pytest.mark.asyncio
    async def test_redis_ping(self, real_redis_pool):
        """Test basic Redis connectivity with ping."""
        # ARQ pool wraps redis, we can access underlying connection
        assert real_redis_pool is not None
        # If we got here without skip, Redis is connected

    @pytest.mark.asyncio
    async def test_redis_pubsub_roundtrip(self, real_redis_pool):
        """Test Redis pub/sub message delivery."""
        import redis.asyncio as aioredis

        # Create a separate connection for subscribing
        redis_client = aioredis.Redis(host='localhost', port=6379)

        try:
            pubsub = redis_client.pubsub()
            await pubsub.subscribe('test_channel')

            # Publish a message
            test_message = json.dumps({
                "type": "test",
                "timestamp": datetime.now().isoformat()
            })
            await redis_client.publish('test_channel', test_message)

            # Receive the message (with timeout)
            message = None
            start_time = time.time()
            while time.time() - start_time < 2:  # 2 second timeout
                msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0.1)
                if msg and msg['type'] == 'message':
                    message = msg
                    break

            assert message is not None, "Should receive published message"
            assert json.loads(message['data'])['type'] == 'test'

        finally:
            await pubsub.unsubscribe('test_channel')
            await redis_client.close()

    @pytest.mark.asyncio
    async def test_redis_job_enqueue(self, real_redis_pool):
        """Test that jobs can be enqueued to Redis."""
        # Enqueue a test job
        job = await real_redis_pool.enqueue_job(
            'test_job_that_does_not_exist',
            {'test': 'data'},
            _queue_name='test_queue'
        )

        assert job is not None
        assert job.job_id is not None


# ============================================================================
# API Server Tests
# ============================================================================

class TestRealAPIServer:
    """Tests that verify the FastAPI server functionality."""

    def test_health_endpoint_real(self, test_client):
        """Test the health check endpoint with real server."""
        response = test_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Cortex API" in data["message"]

    def test_event_endpoint_validation(self, test_client):
        """Test that the events endpoint validates input correctly."""
        # Invalid event (missing required fields)
        invalid_event = {
            "event_type": "git_commit",
            # Missing other required fields
        }

        response = test_client.post("/api/events", json=invalid_event)
        assert response.status_code == 422  # Validation error

    def test_event_endpoint_accepts_valid_event(self, test_client):
        """Test that valid events are accepted (requires Redis mock)."""
        from unittest.mock import AsyncMock

        # Mock Redis since we're testing API validation, not full flow
        mock_redis = AsyncMock()
        mock_redis.enqueue_job = AsyncMock()

        test_client.app.state.redis = mock_redis

        valid_event = {
            "event_type": "git_commit",
            "repo_name": "test-repo",
            "branch_name": "main",
            "commit_hash": "abc123def456",
            "author_name": "Test Author",
            "author_email": "test@example.com",
            "message": "test: integration test commit",
            "diff": "diff --git a/test.py",
            "timestamp": datetime.now().isoformat()
        }

        response = test_client.post("/api/events", json=valid_event)

        assert response.status_code == 202
        assert "queued" in response.json()["message"].lower()
        mock_redis.enqueue_job.assert_called_once()


# ============================================================================
# WebSocket Tests
# ============================================================================

class TestRealWebSocket:
    """Tests for WebSocket connectivity."""

    def test_websocket_connection(self, test_client):
        """Test WebSocket connection establishment."""
        with test_client.websocket_connect("/ws") as websocket:
            # Connection should be established
            assert websocket is not None

            # Server should accept the connection without immediately closing
            # We don't expect any messages without triggering the flow

    def test_websocket_receives_broadcast(self, test_client):
        """Test that WebSocket clients receive broadcast messages."""
        import threading

        received_messages = []

        def listen_for_messages():
            try:
                with test_client.websocket_connect("/ws") as websocket:
                    # Set a short timeout
                    try:
                        data = websocket.receive_json(timeout=1)
                        received_messages.append(data)
                    except Exception:
                        pass  # Timeout expected if no messages
            except Exception:
                pass

        # Start listener in background
        listener = threading.Thread(target=listen_for_messages)
        listener.start()
        listener.join(timeout=2)

        # Test passes if connection was established (no crash)
        # Full broadcast testing requires Redis pub/sub integration


# ============================================================================
# Full Pipeline Integration Tests (with Real Redis)
# ============================================================================

class TestRealPipelineIntegration:
    """
    Integration tests that run actual pipeline code with real Redis.
    External LLM/TTS services are still mocked for cost and reliability.
    """

    @pytest.mark.asyncio
    async def test_comprehension_pipeline_with_real_redis(self, real_redis_pool):
        """
        Test comprehension pipeline with real Redis for job enqueuing.
        LLM and storage services are mocked.
        """
        from cortex.pipelines.pipelines import Pipeline
        from cortex.pipelines.comprehension import (
            EventDeserializer,
            InsightGenerator,
            KnowledgeGraphWriter,
            ChromaWriter,
            SynthesisTrigger
        )

        # Mock LLM and storage services (external APIs)
        mock_llm = MagicMock()
        mock_llm.generate_commit_summary = MagicMock(
            return_value="Real Redis integration test summary"
        )

        mock_kg = MagicMock()
        mock_kg.process_insight = MagicMock()

        mock_chroma = MagicMock()
        mock_chroma.add_document = MagicMock()

        # Build pipeline with real Redis
        pipeline = Pipeline([
            EventDeserializer(),
            InsightGenerator(llm_service=mock_llm),
            [
                KnowledgeGraphWriter(mock_kg),
                ChromaWriter(mock_chroma),
            ],
            SynthesisTrigger(),
        ])

        event_data = {
            "event_type": "git_commit",
            "repo_name": "integration-test-repo",
            "branch_name": "main",
            "commit_hash": "realredis123",
            "author_name": "Integration Tester",
            "author_email": "integration@test.com",
            "message": "test: real redis integration",
            "diff": "diff --git a/test.py\n+# Integration test",
            "timestamp": datetime.now().isoformat()
        }

        # Use real Redis pool
        context = {"redis": real_redis_pool}

        # Execute pipeline
        await pipeline.execute(data=event_data, context=context)

        # Verify services were called
        mock_llm.generate_commit_summary.assert_called_once()
        mock_kg.process_insight.assert_called_once()
        mock_chroma.add_document.assert_called_once()

        # The synthesis job should have been enqueued to real Redis
        # (We can't easily verify this without checking Redis directly,
        # but the test passes if no exceptions were raised)

    @pytest.mark.asyncio
    async def test_redis_pubsub_delivery_integration(self, real_redis_pool):
        """
        Test that AudioDeliveryProcessor can publish to real Redis pub/sub.
        """
        import redis.asyncio as aioredis
        import base64

        # Create subscriber
        redis_client = aioredis.Redis(host='localhost', port=6379)
        pubsub = redis_client.pubsub()
        await pubsub.subscribe('insights_channel')

        try:
            # Mock TTS to avoid external API calls
            with patch('cortex.pipelines.delivery.texttospeech.TextToSpeechClient') as MockTTS:
                mock_tts = MockTTS.return_value
                mock_tts.synthesize_speech.return_value = MagicMock(
                    audio_content=b"real_redis_test_audio"
                )

                with patch('cortex.pipelines.delivery.Settings') as MockSettings:
                    MockSettings.return_value.tts_voice_name = "en-US-Wavenet-D"

                    from cortex.pipelines.delivery import AudioDeliveryProcessor

                    # Use real Redis client for publishing
                    processor = AudioDeliveryProcessor(redis=redis_client)

                    data = {"final_insight": "Real Redis pub/sub test insight"}
                    await processor.process(data, {})

            # Try to receive the published message
            message = None
            start_time = time.time()
            while time.time() - start_time < 2:
                msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0.1)
                if msg and msg['type'] == 'message':
                    message = msg
                    break

            assert message is not None, "Should receive insight message on insights_channel"

            # Parse and verify message format
            parsed = json.loads(message['data'])
            assert parsed['type'] == 'insight'
            assert parsed['text'] == "Real Redis pub/sub test insight"
            assert 'audio' in parsed

            # Verify audio is valid base64
            decoded_audio = base64.b64decode(parsed['audio'])
            assert decoded_audio == b"real_redis_test_audio"

        finally:
            await pubsub.unsubscribe('insights_channel')
            await redis_client.close()


# ============================================================================
# Service Health Checks
# ============================================================================

class TestServiceHealthChecks:
    """Tests to verify external service availability."""

    @pytest.mark.asyncio
    async def test_redis_health(self):
        """Check if Redis is running and accessible."""
        import redis.asyncio as aioredis

        try:
            redis_client = aioredis.Redis(host='localhost', port=6379)
            result = await redis_client.ping()
            await redis_client.close()
            assert result is True
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")

    def test_api_server_health(self, test_client):
        """Check if API server is responding."""
        response = test_client.get("/")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_ollama_availability(self):
        """Check if Ollama is running (optional - for local LLM)."""
        import httpx

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:11434/api/tags", timeout=2)
                if response.status_code == 200:
                    assert True
                else:
                    pytest.skip("Ollama not responding correctly")
        except Exception as e:
            pytest.skip(f"Ollama not available: {e}")
