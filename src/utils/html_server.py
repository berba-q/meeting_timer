"""
Simple HTTP server to serve the HTML client page for network display.
"""
import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Dict, Optional
from PyQt6.QtCore import QObject, pyqtSignal
import socket

class CustomHandler(SimpleHTTPRequestHandler):
    """Custom HTTP request handler that serves files from our resources directory"""
    
    def __init__(self, *args, **kwargs):
        self.html_content = kwargs.pop('html_content', None)
        self.ws_port = kwargs.pop('ws_port', 8765)
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/' or self.path == '/index.html':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # If we have custom HTML content, inject WebSocket port and serve it
            if self.html_content:
                html = self.html_content.replace('{WS_PORT}', str(self.ws_port))
                self.wfile.write(html.encode('utf-8'))
            else:
                # Fallback to generic response
                self.wfile.write(b'<html><body><h1>JW Meeting Timer</h1><p>Network display server is running.</p></body></html>')
        else:
            # For any other path, return 404
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')
    
    def log_message(self, format, *args):
        """Suppress log messages"""
        pass


class NetworkHTTPServer(QObject):
    """HTTP server to serve the HTML client interface"""
    
    # Signals
    server_started = pyqtSignal(str, int)  # URL, port
    server_stopped = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # Server properties
        self.server = None
        self.thread = None
        self.host_ip = self._get_local_ip()
        self.port = 8080  # Default HTTP port
        self.html_content = None
        self.ws_port = 8765  # Default WebSocket port
        self.is_running = False
    
    def _get_local_ip(self) -> str:
        """Get the local IP address of this machine"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"
    
    def load_html_content(self, html_path: str) -> bool:
        """Load HTML content from file"""
        try:
            with open(html_path, 'r', encoding='utf-8') as f:
                self.html_content = f.read()
            return True
        except Exception as e:
            self.error_occurred.emit(f"Failed to load HTML content: {str(e)}")
            return False
    
    def set_html_content(self, html_content: str):
        """Set HTML content directly"""
        self.html_content = html_content
    
    def start_server(self, port: Optional[int] = None, ws_port: Optional[int] = None):
        """Start the HTTP server"""
        print(f"Attempting to start HTTP server on {self.host_ip}:{self.port}")
        if self.is_running:
            print("Server is already running, not starting again")
            return
        
        # Update ports if specified
        if port:
            self.port = port
            print(f"Using specified port: {port}")
        
        if ws_port:
            self.ws_port = ws_port
        
        # Define a handler factory that includes our custom parameters
        def handler_factory(*args, **kwargs):
            print("Creating handler for incoming connection")
            return CustomHandler(
                *args, 
                html_content=self.html_content,
                ws_port=self.ws_port,
                **kwargs
            )
        
        def run_server():
            try:
                print(f"Binding server to {self.host_ip}:{self.port}")
                self.server = HTTPServer((self.host_ip, self.port), handler_factory)
                self.is_running = True
                print(f"HTTP server started successfully on {self.host_ip}:{self.port}")
                self.server_started.emit(f"http://{self.host_ip}:{self.port}", self.port)
                self.server.serve_forever()
            except OSError as e:
                self.error_occurred.emit(f"Failed to start HTTP server: {str(e)}")
                self.is_running = False
            except Exception as e:
                self.error_occurred.emit(f"Error in HTTP server: {str(e)}")
                self.is_running = False
        
        # Start the server in a separate thread
        self.thread = threading.Thread(target=run_server, daemon=True)
        self.thread.start()
        print("Server thread started")
    
    def stop_server(self):
        """Stop the HTTP server"""
        if not self.is_running:
            return
        
        # Shutdown the server
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        
        self.is_running = False
        self.server_stopped.emit()
    
    def get_url(self) -> str:
        """Get the URL clients can use to connect"""
        return f"http://{self.host_ip}:{self.port}"