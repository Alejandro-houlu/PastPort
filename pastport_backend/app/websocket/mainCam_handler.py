import asyncio
import json
import base64
import cv2
import numpy as np
from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List
from app.services.mainCam_service import mainCam_recognition_service


class MainCamConnectionManager:
    """Manage WebSocket connections for mainCam recognition"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_configs: Dict[WebSocket, dict] = {}
    
    async def connect(self, websocket: WebSocket):
        print("🔌 MainCam WebSocket: New connection attempt")
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_configs[websocket] = {
            "model_name": "yolo11n-seg-custom-v7.pt",
            "confidence": 0.25,
            "iou_threshold": 0.45
        }
        print(f"✅ MainCam WebSocket: Connection established. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        print("🔌 MainCam WebSocket: Connection disconnecting")
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.connection_configs:
            del self.connection_configs[websocket]
        print(f"❌ MainCam WebSocket: Connection closed. Remaining connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        await websocket.send_text(json.dumps(message))
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_text(json.dumps(message))


manager = MainCamConnectionManager()


async def handle_mainCam_websocket_connection(websocket: WebSocket):
    """Handle WebSocket connection for real-time mainCam recognition"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            message_type = message.get("type")
            print(f"📨 MainCam WebSocket: Received message type '{message_type}'")
            
            if message_type == "config":
                # Update configuration for this connection
                config = message.get("config", {})
                print(f"⚙️ MainCam WebSocket: Updating config: {config}")
                manager.connection_configs[websocket].update(config)
                
                await manager.send_personal_message({
                    "type": "config_updated",
                    "config": manager.connection_configs[websocket]
                }, websocket)
                print("✅ MainCam WebSocket: Config updated and sent to client")
            
            elif message_type == "frame":
                # Process video frame
                frame_id = message.get("frame_id", "unknown")
                print(f"📸 MainCam WebSocket: Processing frame {frame_id}")
                await process_frame_message(websocket, message)
            
            elif message_type == "ping":
                # Respond to ping
                print("🏓 MainCam WebSocket: Received ping, sending pong")
                await manager.send_personal_message({
                    "type": "pong",
                    "timestamp": message.get("timestamp")
                }, websocket)
            
            else:
                print(f"❓ MainCam WebSocket: Unknown message type: {message_type}")
                await manager.send_personal_message({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                }, websocket)
                
    except WebSocketDisconnect:
        print("🔌 MainCam WebSocket: Client disconnected")
        manager.disconnect(websocket)
    except Exception as e:
        print(f"💥 MainCam WebSocket: Connection error: {str(e)}")
        await manager.send_personal_message({
            "type": "error",
            "message": str(e)
        }, websocket)
        manager.disconnect(websocket)


async def process_frame_message(websocket: WebSocket, message: dict):
    """Process incoming video frame for recognition"""
    frame_id = message.get("frame_id", "unknown")
    
    try:
        config = manager.connection_configs[websocket]
        print(f"🔧 MainCam WebSocket: Using config for frame {frame_id}: {config}")
        
        # Extract frame data
        frame_data = message.get("frame_data")
        if not frame_data:
            raise ValueError("No frame data provided")
        
        print(f"📥 MainCam WebSocket: Frame {frame_id} data length: {len(frame_data)} chars")
        
        # Decode frame
        if frame_data.startswith('data:image'):
            frame_data = frame_data.split(',')[1]
            print(f"🔍 MainCam WebSocket: Frame {frame_id} stripped data URL prefix")
        
        frame_bytes = base64.b64decode(frame_data)
        print(f"📊 MainCam WebSocket: Frame {frame_id} decoded to {len(frame_bytes)} bytes")
        
        # Convert to numpy array
        nparr = np.frombuffer(frame_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise ValueError("Failed to decode frame")
        
        print(f"🖼️ MainCam WebSocket: Frame {frame_id} decoded to {frame.shape} image")
        
        # Process with YOLO
        print(f"🤖 MainCam WebSocket: Starting YOLO processing for frame {frame_id}")
        result = await mainCam_recognition_service.process_video_frame(
            frame,
            config["model_name"],
            config["confidence"],
            config["iou_threshold"]
        )
        
        detections = result.get("metadata", {}).get("num_detections", 0)
        processing_time = result.get("metadata", {}).get("processing_time", 0)
        print(f"🎯 MainCam WebSocket: Frame {frame_id} processed - {detections} detections in {processing_time}ms")
        
        # Send result back to client
        await manager.send_personal_message({
            "type": "recognition_result",
            "frame_id": message.get("frame_id"),
            "timestamp": message.get("timestamp"),
            "result": result
        }, websocket)
        print(f"📤 MainCam WebSocket: Frame {frame_id} result sent to client")
        
    except Exception as e:
        print(f"💥 MainCam WebSocket: Frame {frame_id} processing error: {str(e)}")
        await manager.send_personal_message({
            "type": "error",
            "message": f"Frame processing error: {str(e)}",
            "frame_id": message.get("frame_id")
        }, websocket)
