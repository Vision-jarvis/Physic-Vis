from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import asyncio
from typing import Dict, Any

from src.graph.workflow import create_graph

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/generate")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("✅ Client Connected")
    
    try:
        while True:
            # 1. Receive User Prompt
            data = await websocket.receive_text()
            request = json.loads(data)
            prompt = request.get("prompt")
            
            if not prompt:
                continue
                
            print(f"📩 Received Prompt: {prompt}")
            
            # 2. Initialize Graph
            workflow = create_graph()
            app_workflow = workflow.compile()
            
            inputs = {"user_prompt": prompt, "retry_count": 0}
            
            # 3. Stream Events
            async for event in app_workflow.astream_events(inputs, version="v1"):
                event_type = event["event"]
                
                # Filter for relevant Node Output events
                if event_type == "on_chain_end":
                    data = event["data"]["output"]
                    if not data or not isinstance(data, dict):
                        continue
                        
                    # Determine Stage & Payload
                    stage = "processing"
                    payload = {}
                    message = ""
                    
                    if "plan" in data and data["plan"]:
                        stage = "architect"
                        message = "Architect has designed the scene."
                        payload = {"plan": data["plan"]}
                    
                    if "physics_code" in data and data["physics_code"]:
                        stage = "physicist"
                        message = "Physicist has derived equations."
                        payload = data["physics_code"]
                        
                    if "code" in data and data["code"]:
                        stage = "coder"
                        message = "Coder has written Manim script."
                        payload = {"code": data["code"]}
                        
                    if "video_path" in data and data["video_path"]:
                        stage = "complete"
                        message = "Rendering successful!"
                        payload = {"videoUrl": data["video_path"]}
                    
                    if "error" in data and data["error"]:
                        stage = "error"
                        message = f"Error: {data['error']}"
                        
                    # Construct SimulationEvent
                    response = {
                        "type": "update" if stage != "complete" and stage != "error" else ("result" if stage == "complete" else "error"),
                        "stage": stage,
                        "message": message,
                        "payload": payload
                    }
                    
                    # specific handle for video result
                    if stage == "complete":
                        response["videoUrl"] = data["video_path"]
                        
                    await websocket.send_json(response)
                    
    except WebSocketDisconnect:
        print("❌ Client Disconnected")
    except Exception as e:
        print(f"🔥 Server Error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
