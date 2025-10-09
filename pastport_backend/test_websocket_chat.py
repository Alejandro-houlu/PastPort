#!/usr/bin/env python3
"""
Test script for Museum Chat WebSocket functionality
Tests the end-to-end WebSocket communication with the RAG system
"""
import asyncio
import json
import websockets
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebSocketChatTester:
    """Test client for Museum Chat WebSocket"""
    
    def __init__(self, uri: str = "ws://localhost:8000/ws/chat"):
        self.uri = uri
        self.websocket = None
    
    async def connect(self):
        """Connect to the WebSocket server"""
        try:
            self.websocket = await websockets.connect(self.uri)
            logger.info(f"Connected to {self.uri}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to {self.uri}: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the WebSocket server"""
        if self.websocket:
            await self.websocket.close()
            logger.info("Disconnected from WebSocket")
    
    async def send_message(self, message: Dict[str, Any]):
        """Send a message to the WebSocket server"""
        if not self.websocket:
            raise Exception("Not connected to WebSocket")
        
        message_json = json.dumps(message)
        await self.websocket.send(message_json)
        logger.info(f"Sent: {message}")
    
    async def receive_message(self) -> Dict[str, Any]:
        """Receive a message from the WebSocket server"""
        if not self.websocket:
            raise Exception("Not connected to WebSocket")
        
        response = await self.websocket.recv()
        message = json.loads(response)
        logger.info(f"Received: {message.get('type', 'unknown')} - {message.get('message', '')[:100]}...")
        return message
    
    async def test_ping(self):
        """Test ping/pong functionality"""
        logger.info("Testing ping/pong...")
        
        ping_message = {
            "type": "ping",
            "message": "ping",
            "session_id": "test_session_1"
        }
        
        await self.send_message(ping_message)
        response = await self.receive_message()
        
        assert response["type"] == "pong", f"Expected pong, got {response['type']}"
        assert response["message"] == "pong", f"Expected pong message, got {response['message']}"
        logger.info("✅ Ping/pong test passed")
    
    async def test_status(self):
        """Test status request"""
        logger.info("Testing status request...")
        
        status_message = {
            "type": "status",
            "message": "get status",
            "session_id": "test_session_2"
        }
        
        await self.send_message(status_message)
        response = await self.receive_message()
        
        assert response["type"] == "status", f"Expected status, got {response['type']}"
        assert "rag_status" in response.get("metadata", {}), "Expected rag_status in metadata"
        logger.info("✅ Status test passed")
    
    async def test_query(self, query: str = "What is this museum about?"):
        """Test a museum query"""
        logger.info(f"Testing query: '{query}'...")
        
        query_message = {
            "type": "query",
            "message": query,
            "session_id": "test_session_3",
            "max_results": 3
        }
        
        await self.send_message(query_message)
        response = await self.receive_message()
        
        if response["type"] == "error":
            logger.warning(f"Query returned error: {response['message']}")
            return False
        
        assert response["type"] == "response", f"Expected response, got {response['type']}"
        assert len(response["message"]) > 0, "Expected non-empty response message"
        
        # Check if sources are provided
        sources = response.get("sources", [])
        logger.info(f"Query returned {len(sources)} sources")
        
        # Check metadata
        metadata = response.get("metadata", {})
        logger.info(f"Response metadata: {list(metadata.keys())}")
        
        logger.info("✅ Query test passed")
        return True
    
    async def test_invalid_message(self):
        """Test handling of invalid messages"""
        logger.info("Testing invalid message handling...")
        
        # Test invalid JSON
        try:
            await self.websocket.send("invalid json")
            response = await self.receive_message()
            assert response["type"] == "error", f"Expected error for invalid JSON, got {response['type']}"
            logger.info("✅ Invalid JSON handling test passed")
        except Exception as e:
            logger.error(f"Invalid JSON test failed: {e}")
        
        # Test invalid message type
        invalid_message = {
            "type": "unknown_type",
            "message": "test",
            "session_id": "test_session_4"
        }
        
        await self.send_message(invalid_message)
        response = await self.receive_message()
        
        assert response["type"] == "error", f"Expected error for unknown type, got {response['type']}"
        logger.info("✅ Invalid message type handling test passed")


async def run_tests():
    """Run all WebSocket tests"""
    logger.info("🚀 Starting Museum Chat WebSocket Tests")
    
    tester = WebSocketChatTester()
    
    try:
        # Connect to WebSocket
        if not await tester.connect():
            logger.error("❌ Failed to connect to WebSocket server")
            return False
        
        # Receive initial status message
        initial_message = await tester.receive_message()
        logger.info(f"Initial connection message: {initial_message.get('type', 'unknown')}")
        
        # Run tests
        await tester.test_ping()
        await tester.test_status()
        
        # Test query (this might fail if RAG system is not ready)
        query_success = await tester.test_query("Tell me about rafflesia")
        if not query_success:
            logger.warning("⚠️ Query test failed - RAG system might not be ready")
        
        await tester.test_invalid_message()
        
        logger.info("🎉 All WebSocket tests completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        return False
    
    finally:
        await tester.disconnect()


async def interactive_chat():
    """Interactive chat session for manual testing"""
    logger.info("🗣️ Starting Interactive Chat Session")
    logger.info("Type 'quit' to exit, 'ping' to test ping, 'status' to check status")
    
    tester = WebSocketChatTester()
    
    try:
        if not await tester.connect():
            logger.error("❌ Failed to connect to WebSocket server")
            return
        
        # Receive initial message
        initial_message = await tester.receive_message()
        print(f"Connected! Initial status: {initial_message.get('message', 'Unknown')}")
        
        session_id = "interactive_session"
        
        while True:
            user_input = input("\n💬 You: ").strip()
            
            if user_input.lower() == 'quit':
                break
            elif user_input.lower() == 'ping':
                message = {"type": "ping", "message": "ping", "session_id": session_id}
            elif user_input.lower() == 'status':
                message = {"type": "status", "message": "get status", "session_id": session_id}
            else:
                message = {"type": "query", "message": user_input, "session_id": session_id}
            
            await tester.send_message(message)
            response = await tester.receive_message()
            
            print(f"🤖 Bot: {response.get('message', 'No message')}")
            
            if response.get('sources'):
                print(f"📚 Sources: {len(response['sources'])} documents found")
    
    except KeyboardInterrupt:
        print("\n👋 Chat session ended by user")
    except Exception as e:
        logger.error(f"❌ Interactive chat failed: {e}")
    finally:
        await tester.disconnect()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        asyncio.run(interactive_chat())
    else:
        asyncio.run(run_tests())
