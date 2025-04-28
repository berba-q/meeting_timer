"""
Secondary display window for the JW Meeting Timer - Speaker View.
A streamlined, distraction-free fullscreen view focusing on timer and next part.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, 
    QSizePolicy, QFrame, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor, QFont

from src.controllers.timer_controller import TimerController
from src.models.timer import TimerState
from src.views.timer_view import TimerView


class SecondaryDisplay(QMainWindow):
    """Secondary display window for the timer - designed for speakers"""
    
    def __init__(self, timer_controller: TimerController):
        super().__init__(None, Qt.WindowType.Window)
        self.timer_controller = timer_controller
        self.next_part = None
        
        # Set window flags for presentation display - fullscreen with no chrome
        self.setWindowFlags(
            Qt.WindowType.Window | 
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        
        # Setup UI
        self._setup_ui()
        
        # Connect signals
        self._connect_signals()
        
        # Show in fullscreen by default
        self.showFullScreen()
    
    def _setup_ui(self):
        """Setup the UI components"""
        # Set application icon
        from src.utils.resources import get_icon
        self.setWindowIcon(get_icon("app_icon"))
        
        self.setWindowTitle("JW Meeting Timer - Speaker View")
        
        # Set default background to black
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        self.setPalette(palette)
        
        # Style the secondary display with high contrast regardless of theme
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #000000;
                color: #ffffff;
            }
            
            QLabel {
                color: #ffffff;
                font-weight: bold;
            }
            
            QFrame {
                background-color: rgba(50, 50, 50, 150);
                border: 1px solid #ffffff;
                border-radius: 15px;
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout with ample margins for readability
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)
        
        # Large digital timer display - very prominent
        self.timer_view = TimerView(self.timer_controller)
        #self.timer_view.setMinimumHeight(400)
        
        
        self.timer_frame = QFrame()
        self.timer_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.timer_frame.setStyleSheet("""
            background-color: #000000;
            border: 2px solid #333333;
            border-radius: 15px;
        """)
        
        timer_layout = QVBoxLayout(self.timer_frame)
        
        self.timer_label = QLabel("")
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("""
            color: #ffffff;
            font-size: 380px;
            font-weight: bold;
            font-family: 'Courier New', monospace;
        """)
        
        timer_layout.addWidget(self.timer_label)
        
        # Combined information panel for next part and predicted end time
        self.info_frame = QFrame()
        self.info_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.info_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(50, 50, 50, 180);
                border: 2px solid #ffffff;
                border-radius: 15px;
                padding: 15px;
            }
        """)
        
        self.info_layout = QVBoxLayout(self.info_frame)
        self.info_layout.setSpacing(10)
        
        # Create a single label for pre-meeting countdown
        self.countdown_message_label = QLabel("")
        self.countdown_message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown_message_label.setStyleSheet("""
            color: #4a90e2; 
            font-size: 80px;
            font-weight: bold;
        """)
        self.countdown_message_label.setWordWrap(True)
        self.info_layout.addWidget(self.countdown_message_label)
        
        # Next part label - combined "Next Part: [title]"
         # Create but hide the meeting info labels
        self.next_part_label = QLabel("Next Part: ")
        self.next_part_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.next_part_label.setStyleSheet("color: #ffffff; font-size: 60px; font-weight: bold;")
        self.next_part_label.setWordWrap(True)
        self.next_part_label.setVisible(False)
        self.info_layout.addWidget(self.next_part_label)
        
        # Predicted end time
        self.end_time_label = QLabel("Predicted End: ")
        self.end_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.end_time_label.setStyleSheet("color: #ffffff; font-size: 60px; font-weight: bold;")
        self.end_time_label.setVisible(False)
        self.info_layout.addWidget(self.end_time_label)
        
        layout.addWidget(self.next_part_label)
        layout.addWidget(self.end_time_label)
        
        # Add the main components to the layout
        layout.addWidget(self.timer_frame, 7)  # Timer gets more vertical space (7:2 ratio)
        layout.addWidget(self.info_frame, 2)
    
    def _connect_signals(self):
        """Connect controller signals"""
        self.timer_controller.timer.time_updated.connect(self._update_time)
        self.timer_controller.timer.state_changed.connect(self._update_timer_state)
        self.timer_controller.part_changed.connect(self._part_changed)
        self.timer_controller.transition_started.connect(self._transition_started)
        self.timer_controller.predicted_end_time_updated.connect(self._update_predicted_end_time)
        self.timer_controller.meeting_started.connect(self._meeting_started)
        self.timer_controller.meeting_ended.connect(self._meeting_ended)
        self.timer_controller.timer.meeting_countdown_updated.connect(self._update_countdown)
        self.timer_controller.timer.current_time_updated.connect(self._update_current_time)
        
    def _update_current_time(self, time_str: str):
        """Update the current time display when in stopped state"""
        if self.timer_controller.timer.state == TimerState.STOPPED:
            # Update with current time when in stopped state
            self.timer_label.setText(time_str)
            
            # Make sure the time is visible with appropriate styling
            self.timer_label.setStyleSheet("""
                color: #ffffff; 
                font-size: 380px;
                font-weight: bold;
                font-family: 'Courier New', monospace;
            """)
    
    def _update_countdown(self, seconds_remaining: int, message: str):
        """Update the countdown message"""
        if seconds_remaining > 0:
            # If meeting not started, update info panel with countdown
            if self.timer_controller.timer.state == TimerState.STOPPED and self.timer_controller.current_part_index == -1:
                # Show the countdown message in the next_part_label
                self.countdown_message_label.setText(message)
                self.countdown_message_label.setVisible(True)
                self.next_part_label.setVisible(False)
                self.end_time_label.setVisible(False)
            
                
                # Set style for countdown message
                self.next_part_label.setStyleSheet("""
                    color: #4a90e2; 
                    font-size: 60px;
                    font-weight: bold;
                """)
        else:
            # Reset labels when countdown ends
            if self.timer_controller.timer.state == TimerState.STOPPED and self.timer_controller.current_part_index == -1:
                self.next_part_label.setText("")
                self.end_time_label.setText("")
                
    
    def _update_time(self, seconds: int):
        """Update the timer display"""
        # Format time based on positive/negative value
        if seconds < 0:  # Overtime
            minutes = abs(seconds) // 60
            secs = abs(seconds) % 60
            time_str = f"-{minutes:02d}:{secs:02d}"
            color = "#ff4d4d"  # Red for overtime
        else:
            minutes = seconds // 60
            secs = seconds % 60
            time_str = f"{minutes:02d}:{secs:02d}"
            
            # Color based on time remaining
            if seconds <= 60:  # Last minute
                color = "#ffaa00"  # Orange for warning (last minute)
            else:
                color = "#00cc00"  # Green for normal running
        
        # Only update timer if not in STOPPED state (otherwise show current time)
        if self.timer_controller.timer.state != TimerState.STOPPED:
            # Update timer display
            self.timer_label.setText(time_str)
            self.timer_label.setStyleSheet(f"""
                color: {color};
                font-size: 380px;
                font-weight: bold;
                font-family: 'Courier New', monospace;
            """)
    
    def _update_timer_state(self, state: TimerState):
        """Update UI based on timer state"""
        if state == TimerState.PAUSED:
            # Blue color for paused state
            self.timer_label.setStyleSheet("""
                color: #3399ff; 
                font-size: 380px;
                font-weight: bold;
                font-family: 'Courier New', monospace;
            """)
        elif state == TimerState.TRANSITION:
            # Purple color for transition state
            self.timer_label.setStyleSheet("""
                color: #bb86fc; 
                font-size: 380px;
                font-weight: bold;
                font-family: 'Courier New', monospace;
            """)
    
    def _part_changed(self, current_part, index):
        """Update display when current part changes"""
        # Update next part information
        parts = self.timer_controller.parts_list
        
        # Reset styling of next_part_label when part changes
        self.next_part_label.setStyleSheet("""
            color: #ffffff; 
            font-size: 60px;
            font-weight: bold;
        """)
        
        # Check if there's a next part
        if index + 1 < len(parts):
            self.next_part = parts[index + 1]
            self.next_part_label.setText(f"Next Part: {self.next_part.title}")
            
            # Adjust font size based on title length
            self._adjust_font_size(self.next_part_label, 40, self.next_part.title)
        else:
            # No next part (this is the last part)
            self.next_part = None
            self.next_part_label.setText("Last Part")
    
    def _adjust_font_size(self, label, base_size, text):
        """Adjust font size based on text length to ensure readability"""
        font = label.font()
        
        # For very long texts, reduce font size
        if len(text) > 60:
            font.setPointSize(base_size - 10)
        elif len(text) > 50:
            font.setPointSize(base_size - 8)
        elif len(text) > 40:
            font.setPointSize(base_size - 6)
        elif len(text) > 30:
            font.setPointSize(base_size - 4)
        elif len(text) > 20:
            font.setPointSize(base_size - 2)
        else:
            font.setPointSize(base_size)
            
        label.setFont(font)
    
    def _transition_started(self, transition_msg):
        """Handle chairman transition"""
        # In transition mode, show the upcoming part
        if self.next_part:
            # No need to change what's displayed, as we're already showing the next part
            pass
        else:
            # If this is the last transition
            self.next_part_label.setText("Next Part: Meeting conclusion")
    
    def _update_predicted_end_time(self, original_end_time, predicted_end_time):
        """Update the predicted end time display with improved precision"""
        # Format the times
        original_time_str = original_end_time.strftime("%H:%M")
        predicted_time_str = predicted_end_time.strftime("%H:%M")
        
        # Calculate the difference
        time_diff = predicted_end_time - original_end_time
        diff_seconds = int(time_diff.total_seconds())
        
        # Get the exact overtime seconds from the timer controller
        overtime_seconds = 0
        if hasattr(self.timer_controller, '_total_overtime_seconds'):
            overtime_seconds = self.timer_controller._total_overtime_seconds
            
            # Ensure display matches exactly what's in the main UI
            if self.timer_controller.timer.state == TimerState.OVERTIME:
                # Use the exact value from the timer
                diff_seconds = overtime_seconds
        
        # Format the display text with appropriate precision
        if diff_seconds > 0:
            # Show precise time for small overruns, minutes for larger ones
            if diff_seconds < 60:
                # Less than a minute - show seconds
                time_text = f"Predicted End: {predicted_time_str} (+{diff_seconds}s)"
            else:
                # Minutes and seconds format
                minutes = diff_seconds // 60
                seconds = diff_seconds % 60
                if seconds == 0:
                    # Even minutes
                    time_text = f"Predicted End: {predicted_time_str} (+{minutes}m)"
                else:
                    # Minutes and seconds
                    time_text = f"Predicted End: {predicted_time_str} (+{minutes}m {seconds}s)"
            
            # Red color for overtime
            self.end_time_label.setStyleSheet("""
                color: #ff4d4d; 
                font-size: 60px;
                font-weight: bold;
            """)
        elif diff_seconds < 0:
            # Running under time (negative diff)
            abs_diff = abs(diff_seconds)
            if abs_diff < 60:
                # Less than a minute - show seconds
                time_text = f"Predicted End: {predicted_time_str} (-{abs_diff}s)"
            else:
                # Minutes and seconds format
                minutes = abs_diff // 60
                seconds = abs_diff % 60
                if seconds == 0:
                    # Even minutes
                    time_text = f"Predicted End: {predicted_time_str} (-{minutes}m)"
                else:
                    # Minutes and seconds
                    time_text = f"Predicted End: {predicted_time_str} (-{minutes}m {seconds}s)"
            
            # Green color for under time
            self.end_time_label.setStyleSheet("""
                color: #4caf50; 
                font-size: 60px;
                font-weight: bold;
            """)
        else:
            # On time
            time_text = f"Predicted End: {predicted_time_str} (on time)"
            self.end_time_label.setStyleSheet("""
                color: #ffffff; 
                font-size: 60px;
                font-weight: bold;
            """)
    
        # Set the text
        self.end_time_label.setText(time_text)
        
    def _meeting_started(self):
        """Handle meeting start event"""
        # Hide countdown message and show meeting info labels
        self.countdown_message_label.setVisible(False)
        self.next_part_label.setVisible(True)
        self.end_time_label.setVisible(True)
    
    def _meeting_ended(self):
        """Handle meeting end"""
        # Show meeting completed message
        self.next_part_label.setText("Meeting Completed")
        self.end_time_label.setText("")
        
    
    def show(self):
        """Override show to always show in fullscreen"""
        self.showFullScreen()