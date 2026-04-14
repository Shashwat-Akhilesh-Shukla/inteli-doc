import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from backend.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "Intelligent Doc API"}

def test_websocket_chat_stream():
    with patch("backend.api.routes.rag_pipeline") as mock_pipeline:
        async def mock_aquery_stream(query):
            yield '{"type": "token", "content": "Hello"}'
            yield '{"type": "token", "content": " World"}'
            
        mock_pipeline.aquery_stream = mock_aquery_stream
        
        with client.websocket_connect("/ws/v1/chat_stream") as websocket:
            websocket.send_text("What is X?")
            
            data1 = websocket.receive_text()
            assert "Hello" in data1
            
            data2 = websocket.receive_text()
            assert "World" in data2
