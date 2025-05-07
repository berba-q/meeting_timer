#!/usr/bin/env python3
"""
Direct test script for WebSocket and HTTP server functionality
of the JW Meeting Timer application.

This script runs both an HTTP server to serve the display page and
a WebSocket server to broadcast timer data. It can be used to test
the network display functionality without running the full application.
"""

import os
import asyncio
import json
import signal
import threading
import time
from websockets.legacy.server import serve
from http.server import HTTPServer, SimpleHTTPRequestHandler
from websockets.server import WebSocketServerProtocol

# Configuration
HTTP_PORT = 8080
WS_PORT = 8765
HOST = "0.0.0.0"  # Listen on all interfaces

# Track connected WebSocket clients
connected_clients = set()

# Current timer state
timer_state = {
    "time": "00:00",
    "state": "running",
    "part": "Current Test Part",
    "nextPart": "Next Test Part",
    "endTime": "12:30",
    "overtime": 0
}

class CustomHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler to serve the display page"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Create simple HTML with embedded WebSocket client
            html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>JW Meeting Timer Display</title>
    <style>
        body {{
            background-color: #000000;
            color: #ffffff;
            font-family: 'Segoe UI', 'Arial', sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            height: 100vh;
            text-align: center;
            overflow: hidden;
        }}
        
        #timer-display {{
            font-family: 'Courier New', monospace;
            font-size: 25vmin;
            font-weight: bold;
            margin: 0;
            line-height: 1;
        }}
        
        #current-part {{
            font-size: 7vmin;
            font-weight: bold;
            margin: 2vh 5vw;
            max-width: 90vw;
        }}
        
        #next-part {{
            font-size: 5vmin;
            margin: 1vh 5vw;
            padding: 2vh;
            background-color: rgba(50, 50, 50, 0.8);
            border-radius: 15px;
            max-width: 90vw;
        }}
        
        #end-time {{
            font-size: 4vmin;
            margin-top: 2vh;
        }}
        
        #status {{
            position: absolute;
            top: 10px;
            right: 10px;
            padding: 5px 10px;
            background-color: rgba(0, 0, 0, 0.7);
            border-radius: 5px;
            font-size: 14px;
        }}
        
        .running {{ color: #4caf50; }}
        .warning {{ color: #ff9800; }}
        .danger {{ color: #f44336; }}
        .paused {{ color: #2196f3; }}
        .transition {{ color: #bb86fc; }}
        .stopped {{ color: #ffffff; }}
    </style>
</head>
<body>
    <div id="status">Connecting...</div>
    
    <h1 id="timer-display" class="stopped">00:00</h1>
    
    <div id="current-part">Waiting for connection...</div>
    
    <div id="next-part">Next Part: —</div>
    
    <div id="end-time"></div>
    
    <script>
        // Timer display elements
        const timerDisplay = document.getElementById('timer-display');
        const currentPart = document.getElementById('current-part');
        const nextPart = document.getElementById('next-part');
        const endTime = document.getElementById('end-time');
        const status = document.getElementById('status');
        
        // Create WebSocket connection
        const socket = new WebSocket(`ws://${{window.location.hostname}}:{WS_PORT}`);
        
        // Connection opened
        socket.addEventListener('open', function(event) {{
            status.textContent = 'Connected';
            status.style.color = '#4caf50';
        }});
        
        // Connection closed
        socket.addEventListener('close', function(event) {{
            status.textContent = 'Disconnected';
            status.style.color = '#f44336';
            
            // Try to reconnect after 5 seconds
            setTimeout(function() {{
                window.location.reload();
            }}, 5000);
        }});
        
        // Listen for messages
        socket.addEventListener('message', function(event) {{
            try {{
                const data = JSON.parse(event.data);
                
                // Update timer display
                timerDisplay.textContent = data.time;
                
                // Set timer color based on state
                timerDisplay.className = data.state;
                
                // Update part information
                if (data.part) {{
                    currentPart.textContent = data.part;
                }} else {{
                    currentPart.textContent = 'No active part';
                }}
                
                // Update next part if available
                if (data.nextPart) {{
                    nextPart.textContent = `Next Part: ${{data.nextPart}}`;
                }} else {{
                    nextPart.textContent = 'Next Part: —';
                }}
                
                // Update end time if available
                if (data.endTime) {{
                    endTime.textContent = `Predicted End: ${{data.endTime}}`;
                    
                    // Add overtime information if available
                    if (data.overtime > 0) {{
                        const minutes = Math.floor(data.overtime / 60);
                        const seconds = data.overtime % 60;
                        
                        if (minutes > 0) {{
                            endTime.textContent += ` (+${{minutes}}m ${{seconds}}s)`;
                        }} else {{
                            endTime.textContent += ` (+${{seconds}}s)`;
                        }}
                        
                        endTime.style.color = '#f44336';
                    }} else {{
                        endTime.style.color = '#4caf50';
                    }}
                }} else {{
                    endTime.textContent = '';
                }}
            }} catch (error) {{
                console.error('Error parsing message:', error);
            }}
        }});
    </script>
</body>
</html>
"""
            # Replace WebSocket port in the HTML
            html = html.replace('{WS_PORT}', str(WS_PORT))
            
            self.wfile.write(html.encode('utf-8'))
        else:
            # For any other path, return 404
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def log_message(self, format, *args):
        """Suppress log messages by default"""
        # Comment this out if you want to see HTTP access logs
        pass

# WebSocket handler
async def websocket_handler(websocket):
    """Handle WebSocket connections"""
    # Add new client to set
    connected_clients.add(websocket)
    print(f"New client connected from {websocket.remote_address}")
    
    # Send current state immediately
    await websocket.send(json.dumps(timer_state))
    
    try:
        # Keep connection alive, waiting for client messages
        async for message in websocket:
            # We don't expect messages from clients
            print(f"Received message from client: {message}")
    except websockets.exceptions.ConnectionClosed:
        print(f"Client disconnected: {websocket.remote_address}")
    finally:
        # Remove client when disconnected
        connected_clients.remove(websocket)

# Broadcast timer data to all clients
async def broadcast_timer_data(data):
    """Broadcast timer data to all connected clients"""
    if not connected_clients:
        return
    
    # Encode data as JSON
    message = json.dumps(data)
    
    # Send to all clients
    disconnected = set()
    for websocket in connected_clients:
        try:
            await websocket.send(message)
        except websockets.exceptions.ConnectionClosed:
            disconnected.add(websocket)
    
    # Remove disconnected clients
    for websocket in disconnected:
        connected_clients.remove(websocket)

# Timer update task - simulates changing timer values
async def update_timer():
    """Simulate timer updates"""
    seconds = 0
    minutes = 5  # Start at 5 minutes
    
    # Timer states to cycle through
    states = ["running", "warning", "danger", "paused", "transition", "stopped"]
    state_index = 0
    
    while True:
        # Update time
        if states[state_index] == "running" or states[state_index] == "warning":
            # Count down
            seconds -= 1
            if seconds < 0:
                seconds = 59
                minutes -= 1
                if minutes < 0:
                    minutes = 0
                    seconds = 0
                    # Switch to next state
                    state_index = (state_index + 1) % len(states)
        
        # Format time string
        time_str = f"{minutes:02d}:{seconds:02d}"
        
        # Update state based on time
        if states[state_index] == "running" and minutes == 0 and seconds <= 60:
            # Last minute, switch to warning
            states[state_index] = "warning"
        
        # Update global timer state
        timer_state["time"] = time_str
        timer_state["state"] = states[state_index]
        
        # Broadcast to clients
        await broadcast_timer_data(timer_state)
        
        # Cycle through states every 30 seconds
        if seconds % 30 == 0 and seconds != 0:
            state_index = (state_index + 1) % len(states)
            
            # When cycling to "running" state, reset timer to 5 minutes
            if states[state_index] == "running":
                minutes = 5
                seconds = 0
        
        # Wait for next update
        await asyncio.sleep(1)

# Run HTTP server in a separate thread
def run_http_server():
    """Run the HTTP server in a separate thread"""
    print("HTTP server thread started")
    try:
        # Create server with custom handler
        server = HTTPServer((HOST, HTTP_PORT), CustomHandler)
        print(f"HTTP server running at http://localhost:{HTTP_PORT}")
        server.serve_forever()
    except Exception as e:
        print(f"HTTP server error: {e}")

# Main async function
async def main():
    """Main function to run both servers"""
    # Start HTTP server in a separate thread
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    # Start WebSocket server
    print("Starting WebSocket server...")
    async with serve(websocket_handler, HOST, WS_PORT):
        print(f"WebSocket server running at ws://localhost:{WS_PORT}")
        
        # Start timer update task
        timer_task = asyncio.create_task(update_timer())
        
        # Keep the server running until interrupted
        try:
            await asyncio.Future()  # Run forever
        except asyncio.CancelledError:
            # Cleanup on cancel
            timer_task.cancel()
            print("WebSocket server stopped")

# Handle keyboard interrupt
def handle_interrupt():
    """Handle keyboard interrupt (Ctrl+C)"""
    print("\nShutting down servers...")
    # Stop the asyncio event loop
    for task in asyncio.all_tasks():
        task.cancel()
    asyncio.get_event_loop().stop()

if __name__ == "__main__":
    # Set up signal handler for clean shutdown
    loop = asyncio.get_event_loop()
    
    # Register signal handlers
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_interrupt)
    
    try:
        # Run the main coroutine
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        # Cleanup
        loop.close()
        print("Servers shut down")