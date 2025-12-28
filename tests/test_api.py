import pytest
from fastapi.testclient import TestClient
from src.api.server import app
import json

client = TestClient(app)

def test_websocket_generate():
    """
    Verifies that the /ws/generate endpoint:
    1. Accepts connection
    2. Receives JSON prompt
    3. Streams 'update' events (Architect -> Physicist -> ...)
    4. Streams 'result' event
    """
    
    # We cheat a bit: The graph execution is mocked or we expect it to run fully.
    # Since we are using the REAL graph, this might take time and valid API keys.
    # For a quick test, we assume the graph works (since we verified it in Phase 2).
    
    with client.websocket_connect("/ws/generate") as websocket:
        # Send Prompt
        websocket.send_text(json.dumps({"prompt": "Visualize a simple pendulum"}))
        
        # Expect Initial Status
        data = websocket.receive_json()
        assert data["type"] == "update"
        assert data["stage"] == "architect"
        
        # We expect a stream of messages.
        # We'll perform a simple loop until we get 'result' or 'error'
        
        final_video_url = None
        has_error = False
        
        while True:
            try:
                # Set a timeout effectively by using the iterator or just waiting
                # TestClient websocket doesn't support easy timeout in loop, but let's try
                data = websocket.receive_json()
                print(f"Received: {data['type']} - {data.get('stage')}")
                
                if data["type"] == "result":
                    final_video_url = data["videoUrl"]
                    break
                if data["type"] == "error":
                    pytest.fail(f"Server returned error: {data['message']}")
                    has_error = True
                    break
            except Exception as e:
                print(f"Exception during receive: {e}")
                break
                
        if has_error:
            pytest.fail("Server returned an error event.")
            
        assert final_video_url is not None
        assert "http://localhost:8000/static" in final_video_url
        print(f"✅ Integration Test Passed. Video URL: {final_video_url}")
