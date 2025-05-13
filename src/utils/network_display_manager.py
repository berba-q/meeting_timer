"""
Network display manager for OnTime Meeting Timer.
This module integrates the WebSocket and HTTP servers to provide network display functionality.
"""
import os
from typing import Optional, Tuple
from datetime import datetime
from PyQt6.QtCore import QObject, pyqtSignal, QTimer

from src.utils.network_broadcaster import NetworkBroadcaster
from src.utils.html_server import NetworkHTTPServer
from src.controllers.timer_controller import TimerController
from src.models.settings import SettingsManager, NetworkDisplayMode
from src.models.timer import TimerState


class NetworkDisplayManager(QObject):
    """Manager for network display functionality"""
    
    # Signals
    display_started = pyqtSignal(str)  # Connection URL
    display_stopped = pyqtSignal()
    client_connected = pyqtSignal(str)
    client_disconnected = pyqtSignal(str)
    status_updated = pyqtSignal(str, int)  # Status message, client count
    network_ready = pyqtSignal()
    
    def __init__(self, timer_controller: TimerController, settings_manager: SettingsManager):
        super().__init__()
        
        self.timer_controller = timer_controller
        self.settings_manager = settings_manager
        
        # Create servers
        self.broadcaster = NetworkBroadcaster()
        self.http_server = NetworkHTTPServer()
        
        # Set up HTML content
        self._setup_html_content()
        
        # Connect signals
        self._connect_signals()
        
        # Timer for periodic status updates
        self.status_timer = QTimer(self)
        self.status_timer.setInterval(5000)  # 5 seconds
        self.status_timer.timeout.connect(self._update_status)

        # Timer for periodic display refresh even when no signal is emitted
        self.display_refresh_timer = QTimer(self)
        self.display_refresh_timer.setInterval(1000)  # every second
        self.display_refresh_timer.timeout.connect(
            lambda: self._on_time_updated(self.timer_controller.timer.remaining_seconds)
        )
    
    def _setup_html_content(self):
        """Set up the HTML content for the network display"""
        # Get the path to the HTML file in our resources
        html_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'resources', 'network_display.html'
        )
        
        # Try to load HTML content from file
        if os.path.exists(html_path):
            self.http_server.load_html_content(html_path)
        else:
            # Generate basic HTML content if file doesn't exist
            html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OnTime Meeting Timer Display</title>
    <style>
        body {
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
        }
        
        #timer-display {
            font-family: 'Courier New', monospace;
            font-size: 25vmin;
            font-weight: bold;
            margin: 0;
            line-height: 1;
        }
        
        #current-part {
            font-size: 7vmin;
            font-weight: bold;
            margin: 2vh 5vw;
            max-width: 90vw;
        }
        
        #next-part {
            font-size: 5vmin;
            margin: 1vh 5vw;
            padding: 2vh;
            background-color: rgba(50, 50, 50, 0.8);
            border-radius: 15px;
            max-width: 90vw;
        }
        
        #end-time {
            font-size: 4vmin;
            margin-top: 2vh;
        }
        
        #status {
            position: absolute;
            top: 10px;
            right: 10px;
            padding: 5px 10px;
            background-color: rgba(0, 0, 0, 0.7);
            border-radius: 5px;
            font-size: 14px;
        }
        
        .running { color: #4caf50; }
        .warning { color: #ff9800; }
        .danger { color: #f44336; }
        .paused { color: #2196f3; }
        .transition { color: #bb86fc; }
        .stopped { color: #ffffff; }
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
        const socket = new WebSocket(`ws://${window.location.hostname}:{WS_PORT}`);
        
        // Connection opened
        socket.addEventListener('open', function(event) {
            status.textContent = 'Connected';
            status.style.color = '#4caf50';
        });
        
        // Connection closed
        socket.addEventListener('close', function(event) {
            status.textContent = 'Disconnected';
            status.style.color = '#f44336';
            
            // Try to reconnect after 5 seconds
            setTimeout(function() {
                window.location.reload();
            }, 5000);
        });
        
        // Listen for messages
        socket.addEventListener('message', function(event) {
            try {
                const data = JSON.parse(event.data);
                
                // Update timer display
                timerDisplay.textContent = data.time;
                
                // Set timer color based on state
                timerDisplay.className = data.state;
                
                // Update part information
                if (data.part) {
                    currentPart.textContent = data.part;
                } else {
                    currentPart.textContent = 'No active part';
                }
                
                // Update next part if available
                if (data.nextPart) {
                    nextPart.textContent = `Next Part: ${data.nextPart}`;
                } else {
                    nextPart.textContent = 'Next Part: —';
                }
                
                // Update end time if available
                if (data.endTime) {
                    endTime.textContent = `Predicted End: ${data.endTime}`;
                    
                    // Add overtime information if available
                    if (data.overtime > 0) {
                        const minutes = Math.floor(data.overtime / 60);
                        const seconds = data.overtime % 60;
                        
                        if (minutes > 0) {
                            endTime.textContent += ` (+${minutes}m ${seconds}s)`;
                        } else {
                            endTime.textContent += ` (+${seconds}s)`;
                        }
                        
                        endTime.style.color = '#f44336';
                    } else {
                        endTime.style.color = '#4caf50';
                    }
                } else {
                    endTime.textContent = '';
                }
            } catch (error) {
                console.error('Error parsing message:', error);
            }
        });
    </script>
</body>
</html>
"""
            self.http_server.set_html_content(html_content)
    
    def _connect_signals(self):
        """Connect signals between components"""
        # Connect broadcaster signals
        self.broadcaster.client_connected.connect(self.client_connected)
        self.broadcaster.client_disconnected.connect(self.client_disconnected)
        self.broadcaster.broadcast_started.connect(self._on_broadcast_started)
        self.broadcaster.broadcast_stopped.connect(self.display_stopped)
        self.broadcaster.error_occurred.connect(self._handle_error)
        
        # Connect HTTP server signals
        self.http_server.server_started.connect(self._on_server_started)
        self.http_server.server_stopped.connect(self._on_server_stopped)
        self.http_server.error_occurred.connect(self._handle_error)
        
        # Connect timer controller signals
        self.timer_controller.timer.time_updated.connect(self._on_time_updated)
        self.timer_controller.timer.state_changed.connect(self._on_state_changed)
        self.timer_controller.part_changed.connect(self._on_part_changed)
        self.timer_controller.predicted_end_time_updated.connect(self._on_predicted_end_time_updated)
        self.timer_controller.meeting_overtime.connect(self._on_meeting_overtime)
    
    def start_network_display(self, mode: NetworkDisplayMode, 
                             http_port: Optional[int] = None, 
                             ws_port: Optional[int] = None) -> bool:
        """Start the network display"""
        try:
            # Use default ports if not specified
            if http_port is None:
                http_port = self.settings_manager.settings.network_display.http_port

            if ws_port is None:
                ws_port = self.settings_manager.settings.network_display.ws_port

            # Prevent double start
            if self.broadcaster.is_broadcasting:
                print("[DEBUG] Network display already running. Skipping startup.")
                return True

            # Start services based on mode
            if mode == NetworkDisplayMode.WEB_SOCKET_ONLY:
                # Start only WebSocket broadcaster
                self.broadcaster.start_broadcasting(ws_port)
                self.status_timer.start()
                self.display_refresh_timer.start()
                self.network_ready.emit()
                return True
                
            elif mode == NetworkDisplayMode.HTTP_AND_WS:
                # Start both HTTP server and WebSocket broadcaster
                self.http_server.start_server(http_port, ws_port)
                self.broadcaster.start_broadcasting(ws_port)
                self.status_timer.start()
                self.display_refresh_timer.start()
                self.network_ready.emit()
                return True

            return False
                
        except Exception as e:
            self._handle_error(f"Failed to start network display: {str(e)}")
            return False
    
    def stop_network_display(self):
        """Stop the network display"""
        # Stop the HTTP server
        self.http_server.stop_server()
        
        # Stop the WebSocket broadcaster
        self.broadcaster.stop_broadcasting()
        
        # Stop the status timer
        self.status_timer.stop()

        # Stop the periodic display refresh timer
        self.display_refresh_timer.stop()
        
        # Emit signal
        self.display_stopped.emit()
    
    def _on_broadcast_started(self, url: str, port: int):
        """Handle WebSocket broadcast started"""
        # Update status to show WebSocket is running
        self.status_updated.emit(f"WebSocket server running on {url}", 
                               self.broadcaster.get_client_count())
    
    def _on_server_started(self, url: str, port: int):
        """Handle HTTP server started"""
        # Emit signal with connection URL
        self.display_started.emit(url)
    
    def _on_server_stopped(self):
        """Handle HTTP server stopped"""
        # Check if WebSocket is still running
        if not self.broadcaster.is_broadcasting:
            self.display_stopped.emit()
    
    def _update_status(self):
        """Update network display status"""
        # Get client count
        client_count = self.broadcaster.get_client_count()
        
        # Emit status update
        if self.broadcaster.is_broadcasting:
            url = self.http_server.get_url() if self.http_server.is_running else self.broadcaster.get_connection_url()
            self.status_updated.emit(f"Network display active: {url}", client_count)
        else:
            self.status_updated.emit("Network display inactive", 0)
    
    def _handle_error(self, error_message: str):
        """Handle errors from components"""
        print(f"Network display error: {error_message}")
        self.status_updated.emit(f"Error: {error_message}", 0)
    
    def _on_time_updated(self, seconds: int):
        """Handle timer time updates with proper current time and countdown display"""
        # Skip if broadcaster isn't initialized
        if not hasattr(self, 'broadcaster') or not self.broadcaster:
            return
            
        # Initialize variables
        time_str = "00:00"
        state_str = "stopped"
        part_title = ""
        next_part_title = ""
        end_time_str = ""
        overtime_seconds = 0
        countdown_message = ""
        
        # Check if we're in STOPPED state with no active part (pre-meeting)
        if (self.timer_controller.timer.state == TimerState.STOPPED and 
            self.timer_controller.current_part_index < 0):
            
            # Use current time for display in stopped state
            now = datetime.now()
            time_str = now.strftime("%H:%M:%S")
            
            # Check if we have a countdown message
            if hasattr(self.timer_controller.timer, '_target_meeting_time'):
                target = self.timer_controller.timer._target_meeting_time
                if target and target > now:
                    time_diff = target - now
                    seconds_remaining = int(time_diff.total_seconds())
                    
                    if seconds_remaining > 0:
                        hours, remainder = divmod(seconds_remaining, 3600)
                        minutes, seconds = divmod(remainder, 60)
                        
                        if hours > 0:
                            countdown_message = f"Meeting starts in {hours}h {minutes}m {seconds}s"
                        else:
                            countdown_message = f"Meeting starts in {minutes}m {seconds}s"
            
            # In pre-meeting state, don't show next part
            next_part_title = ""
        else:
            # Normal timer operation (during meeting)
            if seconds < 0:  # Overtime
                minutes = abs(seconds) // 60
                secs = abs(seconds) % 60
                time_str = f"-{minutes:02d}:{secs:02d}"
            else:
                minutes = seconds // 60
                secs = seconds % 60
                time_str = f"{minutes:02d}:{secs:02d}"
            
            # Map timer state to string representation
            state_map = {
                TimerState.RUNNING: "running",
                TimerState.PAUSED: "paused",
                TimerState.OVERTIME: "danger",
                TimerState.TRANSITION: "transition",
                TimerState.STOPPED: "stopped",
                TimerState.COUNTDOWN: "running"
            }
            
            state_str = state_map.get(self.timer_controller.timer.state, "stopped")
            
            # If timer is running and less than 60 seconds, use warning color
            if (self.timer_controller.timer.state == TimerState.RUNNING and 
                0 < self.timer_controller.timer.remaining_seconds <= 60):
                state_str = "warning"
            
            # Get current part title
            if self.timer_controller.current_part_index >= 0 and self.timer_controller.parts_list:
                current_part = self.timer_controller.parts_list[self.timer_controller.current_part_index]
                part_title = current_part.title
            
            # Get next part title
            next_part_index = self.timer_controller.current_part_index + 1
            if self.timer_controller.parts_list and next_part_index < len(self.timer_controller.parts_list):
                next_part = self.timer_controller.parts_list[next_part_index]
                next_part_title = next_part.title
            
            # Get predicted end time
            if hasattr(self.timer_controller, '_predicted_end_time') and self.timer_controller._predicted_end_time:
                end_time_str = self.timer_controller._predicted_end_time.strftime("%H:%M")
            
            # Get overtime seconds
            overtime_seconds = getattr(self.timer_controller, '_total_overtime_seconds', 0)
        
        # Debug the data before sending
        print(f"Network update: time={time_str}, state={state_str}, part={part_title}")
        
        # Use the broadcaster's update_timer_data method directly
        self.broadcaster.update_timer_data(
            time_str=time_str,
            state=state_str,
            part_title=part_title,
            next_part=next_part_title,
            end_time=end_time_str,
            overtime_seconds=overtime_seconds,
            countdown_message=countdown_message
        )
    
    def _on_state_changed(self, state: TimerState):
        """Handle timer state changes"""
        # Force an immediate update of the display
        self._on_time_updated(self.timer_controller.timer.remaining_seconds)
    
    def _on_part_changed(self, part, index):
        """Handle part changes"""
        # Force an update to reflect the new part
        self._on_time_updated(self.timer_controller.timer.remaining_seconds)
    
    def _on_predicted_end_time_updated(self, original_end_time, predicted_end_time):
        """Handle predicted end time updates"""
        # Force an update to reflect the new predicted end time
        self._on_time_updated(self.timer_controller.timer.remaining_seconds)
    
    def _on_meeting_overtime(self, total_overtime_seconds):
        """Handle meeting overtime updates"""
        # Force an update to reflect the overtime
        self._on_time_updated(self.timer_controller.timer.remaining_seconds)
    
    def get_connection_info(self) -> Tuple[str, int, int]:
        """Get connection information for network display"""
        http_url = self.http_server.get_url() if self.http_server.is_running else ""
        client_count = self.broadcaster.get_client_count()
        active_services = (
            (1 if self.http_server.is_running else 0) + 
            (1 if self.broadcaster.is_broadcasting else 0)
        )
        
        return (http_url, client_count, active_services)
    
    def cleanup(self):
        """Ensure everything is stopped cleanly"""
        self.stop_network_display()