"""
WebSocket handler for real-time dashboard updates
"""

import json
import asyncio
from typing import Set, Dict, Any
from fastapi import WebSocket
from .agent import dashboard_agent

class DashboardWebSocketManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self._started = False

    async def connect(self, websocket: WebSocket):
        """Connect a new WebSocket client."""
        await websocket.accept()
        self.active_connections.add(websocket)
        
        # Start listening to Firestore updates if not already started
        if not self._started:
            dashboard_agent.start_listening()
            self._started = True
            
            # Start the update loop
            asyncio.create_task(self._broadcast_updates())

    async def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client."""
        self.active_connections.remove(websocket)
        
        # If no more connections, stop listening to Firestore
        if not self.active_connections and self._started:
            dashboard_agent.stop_listening()
            self._started = False

    async def _broadcast_updates(self):
        """Broadcast updates to all connected clients."""
        while self._started:
            # Get current dashboard data
            data = dashboard_agent.get_dashboard_data()
            
            # Broadcast to all connected clients
            for connection in self.active_connections:
                try:
                    await connection.send_json(data)
                except Exception:
                    # Remove failed connections
                    self.active_connections.remove(connection)
            
            # Wait before next update
            await asyncio.sleep(1)  # Update every second

# Create a singleton instance
websocket_manager = DashboardWebSocketManager() 