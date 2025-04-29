"""
Network display server for JW Meeting Timer.
This module provides functionality to broadcast timer data over the network.
"""
import json
import asyncio
import threading
import websockets
import socket
from typing import Dict, Set, Optional, Any, List
from PyQt6.QtCore import QObject, pyqtSignal

class NetworkBroadcaster(QObject):
    """Broadcasts timer data over WebSocket to connected clients"""
    
    # Signals
    client_connected = pyqtSignal(str)
    client_disconnected = pyqtSignal(str)
    broadcast_started = pyqtSignal(str, int)  # URL, port
    broadcast_stopped = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # WebSocket server
        self.server = None
        self.server_task = None
        self.event_loop = None
        self.thread = None
        
        # Connection tracking
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.host_ip = self._get_local_ip()
        self.port = 8765  # Default WebSocket port
        self.is_broadcasting = False
        
        # Current state
        self.current_state = {
            "time": "00:00",
            "state": "stopped",
            "part": "",
            "nextPart": "",
            "endTime": "",
            "overtime": 0
        }
    
    def _get_local_ip(self) -> str:
        """Get the local IP address of this machine"""
        try:
            # Create a socket to determine the IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # No need to actually connect, just configure the socket
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            # Fallback to localhost if we can't determine the IP
            return "127.0.0.1"
    
    async def _handler(self, websocket):
        """Handle WebSocket connections"""
        # Register new client
        self.connected_clients.add(websocket)
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        self.client_connected.emit(client_id)
        
        # Send current state immediately upon connection
        try:
            await websocket.send(json.dumps(self.current_state))
        except Exception as e:
            pass
        
        try:
            # Keep connection open until client disconnects
            async for message in websocket:
                # We don't expect messages from clients, but could handle commands here
                pass
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            # Remove disconnected client
            self.connected_clients.remove(websocket)
            self.client_disconnected.emit(client_id)
    
    async def _server_main(self):
        """Main server coroutine"""
        try:
            # Start WebSocket server
            self.server = await websockets.serve(
                self._handler, 
                self.host_ip, 
                self.port
            )
            
            # Emit signal that broadcast has started
            self.broadcast_started.emit(f"http://{self.host_ip}:{self.port}", self.port)
            self.is_broadcasting = True
            
            # Keep server running
            await asyncio.Future()
        except OSError as e:
            # Handle address already in use or other network errors
            self.error_occurred.emit(f"Failed to start server: {str(e)}")
            self.is_broadcasting = False

    def start_broadcasting(self, port: Optional[int] = None):
        """Start broadcasting timer data over WebSocket"""
        if self.is_broadcasting:
            return
        
        # Update port if specified
        if port:
            self.port = port
        
        # Create a new event loop in a separate thread
        self.event_loop = asyncio.new_event_loop()
        
        def run_server():
            asyncio.set_event_loop(self.event_loop)
            self.server_task = self.event_loop.create_task(self._server_main())
            self.event_loop.run_forever()
        
        # Start the server in a separate thread
        self.thread = threading.Thread(target=run_server, daemon=True)
        self.thread.start()
    
    def stop_broadcasting(self):
        """Stop broadcasting timer data"""
        if not self.is_broadcasting:
            return
        
        # Close server and clean up
        if self.server:
            self.server.close()
            
            # Stop the event loop
            if self.event_loop and self.event_loop.is_running():
                self.event_loop.call_soon_threadsafe(self.event_loop.stop)
        
        self.is_broadcasting = False
        self.broadcast_stopped.emit()
    
    async def _broadcast_to_clients(self, data: Dict[str, Any]):
        """Broadcast data to all connected clients"""
        if not self.connected_clients:
            return
        
        # Convert data to JSON
        json_data = json.dumps(data)
        
        # Send to all connected clients
        disconnected_clients = set()
        for client in self.connected_clients:
            try:
                await client.send(json_data)
            except websockets.exceptions.ConnectionClosed:
                # Mark for removal
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            self.connected_clients.remove(client)
    
    def update_timer_data(self, time_str: str, state: str, part_title: str, 
                        next_part: str = "", end_time: str = "", overtime_seconds: int = 0):
        """Update the current timer data and broadcast to clients"""
        # Update current state
        self.current_state = {
            "time": time_str,
            "state": state,
            "part": part_title,
            "nextPart": next_part,
            "endTime": end_time,
            "overtime": overtime_seconds
        }
        
        # Broadcast to clients if server is running
        if self.is_broadcasting and self.event_loop:
            asyncio.run_coroutine_threadsafe(
                self._broadcast_to_clients(self.current_state), 
                self.event_loop
            )
    
    def get_connection_url(self) -> str:
        """Get the URL clients can use to connect"""
        return f"http://{self.host_ip}:{self.port}"
    
    def get_client_count(self) -> int:
        """Get the number of connected clients"""
        return len(self.connected_clients)