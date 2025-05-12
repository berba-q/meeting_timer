"""
Secondary display window for the OnTime - Speaker View.
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

    def __init__(self, timer_controller: TimerController, settings_controller, parent=None):
        super().__init__(parent, Qt.WindowType.Window)
        self.timer_controller = timer_controller
        self.settings_controller = settings_controller
        # Controls whether the live clock is allowed to update the label
        self.show_clock: bool = True
        self.next_part = None
        self._show_countdown = False
        
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

        # Connect settings changed signal
        self.settings_controller.settings_changed.connect(self._on_settings_updated)

        # Show in fullscreen by default
        self.showFullScreen()
    
    def _setup_ui(self):
        """Setup the UI components"""
        # Set application icon
        from src.utils.resources import get_icon
        self.setWindowIcon(get_icon("app_icon"))
        
        self.setWindowTitle("OnTime - Speaker View")
        
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
        layout.setContentsMargins(40, 20, 40, 20)
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
            font-weight: bold;
            font-family: 'Tahoma', 'Arial Black', sans-serif;
            padding: 0px;
            margin: 0px;
        """)
        self.timer_label.setMinimumSize(0, 0)
        self.timer_label.setWordWrap(True)
        self.timer_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        timer_layout.addWidget(self.timer_label)
        
        # Combined information panel for next part and predicted end time
        # Single info panel below the timer
        self.info_frame = QFrame()
        self.info_frame.setFrameShape(QFrame.Shape.StyledPanel)
        
        info_layout = QVBoxLayout(self.info_frame)
        info_layout.setSpacing(10)
        
        # Label for either countdown message or next part/predicted end
        self.info_label1 = QLabel()
        self.info_label1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_label1.setStyleSheet("""
            color: #ffffff;
            font-weight: bold;
        """)
        self.info_label1.setMinimumSize(0, 0)
        self.info_label1.setWordWrap(True)
        self.info_label1.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.info_label2 = QLabel()
        self.info_label2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # Match info_label1 size
        self.info_label2.setStyleSheet("""
            color: #ff4d4d;
            font-weight: bold;
        """)
        self.info_label2.setMinimumSize(0, 0)
        self.info_label2.setWordWrap(True)
        self.info_label2.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        info_layout.addWidget(self.info_label1)
        info_layout.addWidget(self.info_label2)
        
        # Add the main components to the layout
        layout.addWidget(self.timer_frame, 10)  # Timer gets more vertical space
        layout.addWidget(self.info_frame, 1)   # Info panel gets less vertical space
        
    
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
        if (self.timer_controller.timer.state == TimerState.STOPPED or self.show_countdown) and self.show_clock:
            # Update with current time when in stopped state
            self.timer_label.setText(time_str)
            
            # Make sure the time is visible with appropriate styling
            self.timer_label.setStyleSheet("""
                color: #ffffff;
                font-weight: bold;
            """)
    
    def _update_countdown(self, seconds_remaining: int, message: str):
        """Update the countdown message"""

        # Guard clause: If meeting is not stopped or meeting has started, never show countdown
        if self.timer_controller.timer.state != TimerState.STOPPED or self.timer_controller.current_part_index >= 0:
            self.show_countdown = False
            self._show_countdown = False
            return

        # Block all updates unless explicitly in countdown mode (use internal flag strictly)
        if not getattr(self, "_show_countdown", False):
            return

        if seconds_remaining > 0:
            self.info_label1.setText(message.upper())
            self.info_label2.setText("")
        else:
            # Countdown ended
            self.show_countdown = False
            self._show_countdown = False
            if self.timer_controller.timer.state == TimerState.STOPPED and self.timer_controller.current_part_index == -1:
                self.info_label1.setText("")
                self.info_label2.setText("")
                
    
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
                font-weight: bold;
            """)
    
    def _update_timer_state(self, state: TimerState):
        """Update UI based on timer state"""
        if state == TimerState.PAUSED:
            # Blue color for paused state
            self.timer_label.setStyleSheet("""
                color: #3399ff;
                font-weight: bold;
            """)
        elif state == TimerState.TRANSITION:
            # Purple color for transition state
            self.timer_label.setStyleSheet("""
                color: #bb86fc;
                font-weight: bold;
            """)
    
    def _part_changed(self, current_part, index):
        """Update display when current part changes"""
        # We're in a meeting, show next part and predicted end
        self.show_countdown = False

        # Update next part information
        parts = self.timer_controller.parts_list

        # Reset styling
        self.info_label1.setStyleSheet("""
            color: #ffffff;
            font-weight: bold;
        """)

        # Check if there's a next part
        if index + 1 < len(parts):
            self.next_part = parts[index + 1]
            self.info_label1.setText(f"NEXT PART: {self.next_part.title.upper()}")
        else:
            # No next part (this is the last part)
            self.next_part = None
            self.info_label1.setText("LAST PART")
    
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
            self.info_label1.setText("MEETING CONCLUSION")
    
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
        
        # Don't show predicted end during countdown
        if self.show_countdown:
            self.info_label2.setText("")
            return
            
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
            self.info_label2.setStyleSheet("""
                color: #ff4d4d;
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
            self.info_label2.setStyleSheet("""
                color: #4caf50;
                font-weight: bold;
            """)
        else:
            # On time
            time_text = f"Predicted End: {predicted_time_str} (on time)"
            self.info_label2.setStyleSheet("""
                color: #ffffff;
                font-weight: bold;
            """)

        # Set the text, and make it uppercase like info_label1
        self.info_label2.setText(time_text)
        self.info_label2.setText(time_text.upper())
        
    def _meeting_started(self):
        """Handle meeting start event"""
        # Suppress the real‑time clock while the meeting is running
        self.show_clock = False
        # Meeting started, switch from countdown to part info
        self.show_countdown = False
        # Immediately clear countdown labels
        self.info_label1.setText("")
        self.info_label2.setText("")
        try:
            self.timer_controller.timer.meeting_countdown_updated.disconnect(self._update_countdown)
            
        except TypeError:
            print("[DEBUG] Signal already disconnected or not connected")

        # Set initial next part info
        if len(self.timer_controller.parts_list) > 1:
            next_part = self.timer_controller.parts_list[1]
            self.info_label1.setText(f"NEXT PART: {next_part.title.upper()}")
            self.info_label1.setStyleSheet("""
                color: #ffffff;
                font-weight: bold;
            """)
            # Show the info labels for meeting info
            self.info_label2.setVisible(True)
        else:
            # No next part (only one part in the meeting)
            self.info_label1.setText("LAST PART")
            self.info_label2.setVisible(True)
    
    def _meeting_ended(self):
        """Handle meeting end"""
        # Re‑enable the clock after the meeting ends
        self.show_clock = True
        # Show meeting completed message
        self.info_label1.setText("MEETING COMPLETED")
        self.info_label2.setText("")
        
    
    def show(self):
        """Override show to always show in fullscreen"""
        self.showFullScreen()
        
    def _adjust_font_sizes(self):
        width = self.width()

        # Dynamically scale the timer font using QFontMetrics for precise fit
        if hasattr(self, "timer_label"):
            from PyQt6.QtGui import QFontMetrics
            text = self.timer_label.text() or "00:00"

            char_count = len(text)
            sample_text = text + " "  # add slight margin
            max_width = self.timer_label.width()
            font = self.timer_label.font()
            safe_width = int(max_width * 0.95)
            # Scale larger for shorter text
            max_font_size = 1400 if char_count <= 5 else 1000 if char_count <= 7 else 800
            for size in range(max_font_size, 100, -2):
                font.setPointSize(size)
                metrics = QFontMetrics(font)
                if (metrics.horizontalAdvance(sample_text) <= safe_width and
                    metrics.height() <= self.timer_label.height() * 0.95):
                    self.timer_label.setFont(font)
                    break

        # Dynamically scale the info labels based on height and width
        if hasattr(self, "info_label1"):
            from PyQt6.QtGui import QFontMetrics
            text1 = self.info_label1.text() or "SAMPLE"
            font = self.info_label1.font()
            for size in range(100, 60, -2):
                font.setPointSize(size)
                metrics = QFontMetrics(font)
                if (metrics.height() <= self.info_label1.height() * 0.60 and
                    metrics.horizontalAdvance(text1) <= self.info_label1.width() * 0.95):
                    self.info_label1.setFont(font)
                    break

        if hasattr(self, "info_label2"):
            text2 = self.info_label2.text() or "SAMPLE"
            font = self.info_label2.font()
            for size in range(100, 60, -2):
                font.setPointSize(size)
                metrics = QFontMetrics(font)
                if (metrics.height() <= self.info_label2.height() * 0.60 and
                    metrics.horizontalAdvance(text2) <= self.info_label2.width() * 0.95):
                    self.info_label2.setFont(font)
                    break

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._adjust_font_sizes()

    def showEvent(self, event):
        super().showEvent(event)
        self._adjust_font_sizes()
        
    def closeEvent(self, event):
        """Handle close event"""
        # Force the window to close when the main window is closed
        #self.timer_controller.stop_timer()
        
        event.accept()
        
    def _on_settings_updated(self):
        #print("[DEBUG] SecondaryDisplay: settings changed signal received")
        self._move_to_configured_screen()

    def _move_to_configured_screen(self):
        settings = self.settings_controller.get_settings()
        screen_name = settings.display.secondary_screen_name
        screens = QApplication.screens()
        for screen in screens:
            if screen.name() == screen_name:
                #print(f"[DEBUG] Moving secondary display to screen: {screen.name()}")
                self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
                self.showNormal()

                # Move to correct geometry manually
                self.setGeometry(screen.geometry())
                #print(f"[DEBUG] Set window geometry to: {screen.geometry()}")

                # Move to screen explicitly
                self.windowHandle().setScreen(screen)

                # Restore topmost and fullscreen
                self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
                self.showFullScreen()
                break
    @property
    def show_countdown(self):
        return self._show_countdown

    @show_countdown.setter
    def show_countdown(self, value):
        if self.timer_controller.timer.state != TimerState.STOPPED or self.timer_controller.current_part_index >= 0:
            
            return
        self._show_countdown = value