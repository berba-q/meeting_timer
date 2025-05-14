"""
This module provides functionality to broadcast timer data over the network.
"""
from datetime import datetime
import json
import functools
import asyncio
import threading
import websockets
from websockets.legacy.server import serve, WebSocketServerProtocol
import socket
import time
import traceback
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
        self.connected_clients: Set[WebSocketServerProtocol] = set()
        self.host_ip = self._get_local_ip()
        self.port = 8765  # Default WebSocket port
        self.is_broadcasting = False
        self._stop_event = threading.Event()
        
        # Current state
        current_time = datetime.now().strftime("%H:%M:%S")
        self.current_state = {
            "time": current_time,
            "state": "stopped",
            "part": "",
            "nextPart": "",
            "endTime": "",
            "overtime": 0,
            "countdownMessage": "",
            "meetingEnded": False
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
    
    async def _handler(self, websocket, path):
        """Handle WebSocket connections with improved error handling"""
        # Register new client
        self.connected_clients.add(websocket)
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        print(f"Client connected: {client_id}")
        self.client_connected.emit(client_id)
        
        # Send current state immediately upon connection
        try:
            serialized = json.dumps(self.current_state)
            print(f"Sending to client {client_id}: {serialized}")
            await websocket.send(serialized)
        except (TypeError, ValueError) as e:
            traceback.print_exc()
        
        try:
            # Keep connection open and handle messages from clients
            async for message in websocket:
                try:
                    # Try to parse the message as JSON
                    data = json.loads(message)
                    
                    # Handle 'request_state' message type
                    if data.get('type') == 'request_state':
                        # Re-send the current state
                        await websocket.send(json.dumps(self.current_state))
                        print(f"Re-sent state to client {client_id} after request")
                except Exception as e:
                    print(f"Error processing message from client {client_id}: {e}")
        except Exception as e:
            if isinstance(e, ConnectionResetError) or isinstance(e, websockets.exceptions.ConnectionClosed):
                print(f"Client connection closed: {client_id}")
            else:
                print(f"Error in WebSocket handler for {client_id}: {e}")
        finally:
            # Remove disconnected client
            self.connected_clients.remove(websocket)
            self.client_disconnected.emit(client_id)
            #print(f"Client disconnected: {client_id}")
    
    async def _server_main(self):
        """Main server coroutine with improved error handling"""
        try:
            # Start WebSocket server
            #print(f"Starting WebSocket server on {self.host_ip}:{self.port}")
            
            # Create server with ping/pong enabled for better connection management
            self.server = await serve(
                self._handler,
                "0.0.0.0",
                self.port,
                ping_interval=30,
                ping_timeout=10
            )
            
            # Emit signal that broadcast has started
            connection_url = f"ws://{self.host_ip}:{self.port}"
            #print(f"WebSocket server started at {connection_url}")
            self.broadcast_started.emit(connection_url, self.port)
            self.is_broadcasting = True
            
            # Keep server running until stopped
            stop_future = asyncio.get_event_loop().create_future()
            self._stop_future = stop_future
            await stop_future
            
        except OSError as e:
            # Handle address already in use or other network errors
            error_msg = f"Failed to start WebSocket server: {str(e)}"
            print(error_msg)
            self.error_occurred.emit(error_msg)
            self.is_broadcasting = False
        except Exception as e:
            error_msg = f"Error in WebSocket server: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            self.error_occurred.emit(error_msg)
            self.is_broadcasting = False

    def start_broadcasting(self, port: Optional[int] = None):
        """Start broadcasting timer data over WebSocket"""
        if self.is_broadcasting:
            print("WebSocket broadcaster already running")
            return
        
        # Update port if specified
        if port:
            self.port = port
            print(f"Using specified WebSocket port: {port}")
        
        # Reset stop event
        self._stop_event.clear()
        
        # Create a new event loop in a separate thread
        self.event_loop = asyncio.new_event_loop()
        
        def run_server():
            try:
                asyncio.set_event_loop(self.event_loop)
                self.server_task = self.event_loop.create_task(self._server_main())
                try:
                    self.event_loop.run_until_complete(self.server_task)
                except RuntimeError as e:
                    if "Event loop stopped before Future completed" in str(e):
                        print("[INFO] Event loop stopped cleanly before Future completed.")
                    else:
                        raise
            except Exception as e:
                print(f"Error in WebSocket server thread: {e}")
                traceback.print_exc()
            finally:
                print("WebSocket server thread finishing")
                if self.event_loop.is_running():
                    self.event_loop.stop()
                    self.event_loop.close()
        
        # Start the server in a separate thread
        self.thread = threading.Thread(target=run_server, daemon=True)
        self.thread.start()
        print("WebSocket broadcaster thread started")
        
        # Small delay to let the server start
        time.sleep(0.5)
    
    def stop_broadcasting(self):
        """Stop broadcasting timer data"""
        if not self.is_broadcasting:
            print("WebSocket broadcaster not running")
            return
        
        print("Stopping WebSocket broadcaster...")
        # Set stop event
        self._stop_event.set()
        
        # Complete the stop future to exit the server loop
        if hasattr(self, '_stop_future') and self._stop_future and not self._stop_future.done():
            if self.event_loop and self.event_loop.is_running():
                self.event_loop.call_soon_threadsafe(lambda: self._stop_future.set_result(None))
        
        # Close server and clean up
        if self.server:
            async def shutdown_server():
                self.server.close()
                await self.server.wait_closed()

            if self.event_loop and self.event_loop.is_running():
                asyncio.run_coroutine_threadsafe(shutdown_server(), self.event_loop)
            
        # Stop the event loop
        if self.event_loop and self.event_loop.is_running():
            self.event_loop.call_soon_threadsafe(self.event_loop.stop)
        
        # Wait for thread to terminate with timeout
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
            print("WebSocket broadcaster thread joined")
            self.thread = None
            self.server = None
            self.server_task = None
            self.event_loop = None
        
        self.is_broadcasting = False
        self.broadcast_stopped.emit()
        print("WebSocket broadcaster stopped")
    
    async def _broadcast_to_clients(self, data: Dict[str, Any]):
        """Broadcast data to all connected clients with improved error handling"""
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
            except Exception as e:
                print(f"Error sending to client {client.remote_address}: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            if client in self.connected_clients:
                self.connected_clients.remove(client)
                try:
                    client_id = f"{client.remote_address[0]}:{client.remote_address[1]}"
                    self.client_disconnected.emit(client_id)
                    print(f"Client disconnected during broadcast: {client_id}")
                except:
                    pass  # Client might not have remote_address anymore
    
    def update_timer_data(self, time_str: str, state: str, part_title: str, 
                next_part: str = "", end_time: str = "", overtime_seconds: int = 0,
                countdown_message: str = "", meeting_ended: bool = False):
        """Update the current timer data and broadcast to clients"""
        # Update current state
        self.current_state = {
            "time": time_str,
            "state": state,
            "part": part_title,
            "nextPart": next_part,
            "endTime": end_time,
            "overtime": overtime_seconds,
            "countdownMessage": countdown_message,
            "meetingEnded": meeting_ended
        }
        
        # Broadcast to clients if server is running
        if self.is_broadcasting and self.event_loop:
            try:
                asyncio.run_coroutine_threadsafe(
                    self._broadcast_to_clients(self.current_state), 
                    self.event_loop
                )
            except Exception as e:
                print(f"Error broadcasting timer data: {e}")
    
    def get_connection_url(self) -> str:
        """Get the URL clients can use to connect"""
        return f"ws://{self.host_ip}:{self.port}"

    def get_client_count(self) -> int:
        """Get the number of connected clients"""
        return len(self.connected_clients)
