import pytest
import os
from app.services.speech import generate_cache_key, synthesize_speech, get_audio_cache_dir


class TestSpeechService:
    """Test speech synthesis, caching, and audio streaming endpoints."""

    def test_cache_key_generation(self):
        k1 = generate_cache_key("about", "A story about lions.", "relaxed", "en-US-AnaNeural")
        k2 = generate_cache_key("about", "A story about lions.", "relaxed", "en-US-AnaNeural")
        k3 = generate_cache_key("about", "A story about dogs.", "relaxed", "en-US-AnaNeural")

        assert k1 == k2
        assert k1 != k3

    def test_audio_endpoint_validation(self, client):
        # Missing word parameter
        res = client.get('/api/audio/speak')
        assert res.status_code == 400
        assert b"Word parameter is required" in res.data

    def test_audio_endpoint_stream(self, client):
        # Request valid word audio
        res = client.get('/api/audio/speak?word=school&context=Our+school+library&speed=relaxed')
        assert res.status_code == 200
        assert res.content_type == 'audio/mpeg'
        assert len(res.data) > 0
