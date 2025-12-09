"""
Unit tests for delivery pipeline processors.
Tests: AudioDeliveryProcessor
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import base64
import json

from cortex.pipelines.delivery import AudioDeliveryProcessor
from cortex.exceptions import ProcessorError


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_redis():
    """Fixture for a mocked Redis client."""
    redis = AsyncMock()
    redis.publish = AsyncMock()
    return redis


@pytest.fixture
def mock_tts_client():
    """Fixture for a mocked Google Cloud Text-to-Speech client."""
    with patch('cortex.pipelines.delivery.texttospeech.TextToSpeechClient') as MockTTS:
        instance = MockTTS.return_value
        yield instance


@pytest.fixture
def mock_settings():
    """Fixture for mocked Settings."""
    with patch('cortex.pipelines.delivery.Settings') as MockSettings:
        instance = MockSettings.return_value
        instance.tts_voice_name = "en-US-Wavenet-D"
        yield instance


@pytest.fixture
def processor(mock_redis, mock_tts_client, mock_settings):
    """Fixture for AudioDeliveryProcessor with mocked dependencies."""
    return AudioDeliveryProcessor(redis=mock_redis)


# ============================================================================
# AudioDeliveryProcessor Tests
# ============================================================================

class TestAudioDeliveryProcessor:
    """Tests for AudioDeliveryProcessor."""

    @pytest.mark.asyncio
    async def test_process_success(self, processor, mock_redis, mock_tts_client):
        """Test successful audio generation and publishing."""
        # Setup mock TTS response
        mock_audio_content = b"fake_audio_data"
        mock_tts_client.synthesize_speech.return_value = MagicMock(
            audio_content=mock_audio_content
        )

        data = {"final_insight": "This is a test insight."}
        result = await processor.process(data, {})

        # Verify TTS was called with correct parameters
        mock_tts_client.synthesize_speech.assert_called_once()
        call_args = mock_tts_client.synthesize_speech.call_args

        # Check input text
        assert call_args.kwargs["input"].text == "This is a test insight."

        # Check voice parameters
        assert call_args.kwargs["voice"].language_code == "en-US"
        assert call_args.kwargs["voice"].name == "en-US-Wavenet-D"

        # Verify Redis publish was called
        mock_redis.publish.assert_called_once()
        publish_args = mock_redis.publish.call_args

        assert publish_args[0][0] == "insights_channel"

        # Verify the message structure
        message = json.loads(publish_args[0][1])
        assert message["type"] == "insight"
        assert message["text"] == "This is a test insight."
        assert message["audio"] == base64.b64encode(mock_audio_content).decode('utf-8')

        # Verify data is returned unchanged
        assert result == data

    @pytest.mark.asyncio
    async def test_process_no_final_insight(self, processor, mock_redis, mock_tts_client):
        """Test handling of missing final_insight."""
        data = {"other_key": "value"}
        result = await processor.process(data, {})

        # Should return data without calling TTS or Redis
        mock_tts_client.synthesize_speech.assert_not_called()
        mock_redis.publish.assert_not_called()
        assert result == data

    @pytest.mark.asyncio
    async def test_process_empty_final_insight(self, processor, mock_redis, mock_tts_client):
        """Test handling of empty final_insight."""
        data = {"final_insight": ""}
        result = await processor.process(data, {})

        # Empty string is falsy, should skip processing
        mock_tts_client.synthesize_speech.assert_not_called()
        mock_redis.publish.assert_not_called()
        assert result == data

    @pytest.mark.asyncio
    async def test_process_none_final_insight(self, processor, mock_redis, mock_tts_client):
        """Test handling of None final_insight."""
        data = {"final_insight": None}
        result = await processor.process(data, {})

        mock_tts_client.synthesize_speech.assert_not_called()
        mock_redis.publish.assert_not_called()
        assert result == data

    @pytest.mark.asyncio
    async def test_process_tts_failure(self, processor, mock_tts_client):
        """Test error handling when TTS fails."""
        mock_tts_client.synthesize_speech.side_effect = Exception("TTS API error")

        data = {"final_insight": "Test insight"}

        with pytest.raises(ProcessorError, match="Error during audio generation or publishing"):
            await processor.process(data, {})

    @pytest.mark.asyncio
    async def test_process_redis_publish_failure(self, processor, mock_redis, mock_tts_client):
        """Test error handling when Redis publish fails."""
        mock_tts_client.synthesize_speech.return_value = MagicMock(
            audio_content=b"audio_data"
        )
        mock_redis.publish.side_effect = Exception("Redis connection error")

        data = {"final_insight": "Test insight"}

        with pytest.raises(ProcessorError, match="Error during audio generation or publishing"):
            await processor.process(data, {})

    @pytest.mark.asyncio
    async def test_process_no_audio_returned(self, processor, mock_redis, mock_tts_client):
        """Test handling when TTS returns no audio data."""
        mock_tts_client.synthesize_speech.return_value = MagicMock(
            audio_content=None
        )

        data = {"final_insight": "Test insight"}
        result = await processor.process(data, {})

        # Should not publish to Redis when no audio
        mock_redis.publish.assert_not_called()
        assert result == data

    @pytest.mark.asyncio
    async def test_process_empty_audio_returned(self, processor, mock_redis, mock_tts_client):
        """Test handling when TTS returns empty audio data."""
        mock_tts_client.synthesize_speech.return_value = MagicMock(
            audio_content=b""
        )

        data = {"final_insight": "Test insight"}
        result = await processor.process(data, {})

        # Empty bytes is falsy, should not publish
        mock_redis.publish.assert_not_called()
        assert result == data

    @pytest.mark.asyncio
    async def test_process_preserves_other_data(self, processor, mock_redis, mock_tts_client):
        """Test that other data in the dict is preserved."""
        mock_tts_client.synthesize_speech.return_value = MagicMock(
            audio_content=b"audio_data"
        )

        data = {
            "final_insight": "Test insight",
            "other_key": "other_value",
            "nested": {"key": "value"}
        }
        result = await processor.process(data, {})

        assert result["other_key"] == "other_value"
        assert result["nested"]["key"] == "value"

    @pytest.mark.asyncio
    async def test_audio_encoding_format(self, processor, mock_redis, mock_tts_client):
        """Test that audio is correctly encoded to base64."""
        test_audio = b"\x00\x01\x02\x03\xff\xfe\xfd"
        mock_tts_client.synthesize_speech.return_value = MagicMock(
            audio_content=test_audio
        )

        data = {"final_insight": "Test insight"}
        await processor.process(data, {})

        message = json.loads(mock_redis.publish.call_args[0][1])
        decoded_audio = base64.b64decode(message["audio"])
        assert decoded_audio == test_audio

    @pytest.mark.asyncio
    async def test_message_json_format(self, processor, mock_redis, mock_tts_client):
        """Test that the published message is valid JSON."""
        mock_tts_client.synthesize_speech.return_value = MagicMock(
            audio_content=b"audio"
        )

        data = {"final_insight": "Test insight"}
        await processor.process(data, {})

        published_message = mock_redis.publish.call_args[0][1]

        # Should be valid JSON
        parsed = json.loads(published_message)
        assert isinstance(parsed, dict)
        assert "type" in parsed
        assert "text" in parsed
        assert "audio" in parsed

    @pytest.mark.asyncio
    async def test_uses_mp3_encoding(self, processor, mock_tts_client):
        """Test that MP3 encoding is requested from TTS."""
        mock_tts_client.synthesize_speech.return_value = MagicMock(
            audio_content=b"audio"
        )

        data = {"final_insight": "Test"}
        await processor.process(data, {})

        call_args = mock_tts_client.synthesize_speech.call_args
        # Check that audio config specifies MP3
        audio_config = call_args.kwargs["audio_config"]
        # The audio_encoding should be MP3 (value 2 in the protobuf enum)
        from google.cloud import texttospeech
        assert audio_config.audio_encoding == texttospeech.AudioEncoding.MP3
