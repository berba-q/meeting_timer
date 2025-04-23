"""
Secondary display window for the JW Meeting Timer - Speaker View.
A completely minimal, distraction-free fullscreen view with no user interaction.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, 
    QSizePolicy, QFrame, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor, QFont

from src.controllers.timer_controller import TimerController
from src.views.timer_view import TimerView


class SecondaryDisplay(QMainWindow):
    """Secondary display window for the timer - designed for speakers"""
    
    def __init__(self, timer_controller: TimerController):
        super().__init__(None, Qt.WindowType.Window)
        self.timer_controller = timer_controller
        
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
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout with ample margins for readability
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)
        
        # Large timer view - primary focus
        self.timer_view = TimerView(self.timer_controller)
        self.timer_view.setMinimumHeight(400)
        
        # Scale up the timer font
        if hasattr(self.timer_view, 'timer_label'):
            font = self.timer_view.timer_label.font()
            font.setPointSize(160)  # Much larger for better visibility
            self.timer_view.timer_label.setFont(font)
        
        # Make part label larger
        font = QFont()
        font.setPointSize(28)
        font.setBold(True)
        self.timer_view.part_label.setFont(font)
        self.timer_view.part_label.setStyleSheet("color: white; font-weight: bold;")
        
        # Part information panel
        self.part_frame = QFrame()
        self.part_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.part_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 30);
                border-radius: 15px;
                padding: 20px;
            }
        """)
        
        part_layout = QVBoxLayout(self.part_frame)
        part_layout.setSpacing(15)
        
        # Current part title - large and prominent
        self.current_part_label = QLabel("Current Part")
        self.current_part_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_part_label.setStyleSheet("color: white; font-size: 36px; font-weight: bold;")
        self.current_part_label.setWordWrap(True)
        
        # Presenter name
        self.presenter_label = QLabel("")
        self.presenter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.presenter_label.setStyleSheet("color: white; font-size: 28px;")
        
        part_layout.addWidget(self.current_part_label)
        part_layout.addWidget(self.presenter_label)
        
        # Add the main components to the layout
        # Timer gets more vertical space (3:1 ratio)
        layout.addWidget(self.timer_view, 3)
        layout.addWidget(self.part_frame, 1)
        
        # Status indicators at the bottom
        self.status_frame = QFrame()
        self.status_frame.setStyleSheet("""
            background-color: transparent;
            border: none;
        """)
        status_layout = QVBoxLayout(self.status_frame)
        status_layout.setSpacing(10)
        
        # Predicted end time will be created when needed
        self.end_time_label = None
        
        # Overtime indicator will be created when needed
        self.overtime_label = None
        
        # Add status frame to main layout with minimal space
        layout.addWidget(self.status_frame, 0)
    
    def _connect_signals(self):
        """Connect controller signals"""
        self.timer_controller.part_changed.connect(self._part_changed)
        self.timer_controller.transition_started.connect(self._transition_started)
        self.timer_controller.meeting_overtime.connect(self._meeting_overtime)
        self.timer_controller.predicted_end_time_updated.connect(self._update_predicted_end_time)
        self.timer_controller.meeting_ended.connect(self._meeting_ended)
    
    def _part_changed(self, part, index):
        """Handle part change"""
        # Update part title with auto-sizing based on length
        self.current_part_label.setText(part.title)
        
        # Handle font sizing for very long titles
        self._adjust_font_size(self.current_part_label, 36, part.title)
        
        # Show presenter if available
        if part.presenter:
            self.presenter_label.setText(part.presenter)
            self.presenter_label.setVisible(True)
        else:
            self.presenter_label.setText("")
            self.presenter_label.setVisible(False)
    
    def _adjust_font_size(self, label, base_size, text):
        """Adjust font size based on text length to ensure readability"""
        font = label.font()
        font.setPointSize(base_size)
        
        # For very long texts, reduce font size
        if len(text) > 40:
            font.setPointSize(base_size - 6)
        elif len(text) > 30:
            font.setPointSize(base_size - 4)
        elif len(text) > 20:
            font.setPointSize(base_size - 2)
            
        label.setFont(font)
    
    def _transition_started(self, transition_msg):
        """Handle chairman transition"""
        # Update display with chairman transition message
        self.current_part_label.setText(transition_msg)
        self._adjust_font_size(self.current_part_label, 36, transition_msg)
        
        self.presenter_label.setText("Chairman")
        self.presenter_label.setVisible(True)
        
        # Update timer label style for transition mode
        if hasattr(self.timer_view, 'timer_label'):
            self.timer_view.timer_label.setStyleSheet("color: purple; font-weight: bold;")
    
    def _meeting_overtime(self, total_overtime_seconds):
        """Handle meeting overtime notification"""
        if total_overtime_seconds > 0:
            # Create overtime indicator if it doesn't exist yet
            if not self.overtime_label:
                self.overtime_label = QLabel()
                self.overtime_label.setStyleSheet("""
                    color: white; 
                    background-color: rgba(255, 0, 0, 0.8);
                    border-radius: 10px;
                    padding: 10px 20px;
                    font-size: 24px;
                    font-weight: bold;
                """)
                self.overtime_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.status_frame.layout().addWidget(self.overtime_label)
            
            # Format the overtime
            minutes = total_overtime_seconds // 60
            seconds = total_overtime_seconds % 60
            
            # Update the label
            if minutes > 0:
                self.overtime_label.setText(f"Meeting Overtime: {minutes}:{seconds:02d}")
            else:
                self.overtime_label.setText(f"Meeting Overtime: {seconds} sec")
                
            self.overtime_label.setVisible(True)
    
    def _update_predicted_end_time(self, original_end_time, predicted_end_time):
        """Update the predicted end time display"""
        from src.controllers.settings_controller import SettingsController
        from src.models.settings import SettingsManager
        
        # Check settings to see if we should show the predicted end time
        settings_manager = self.timer_controller.meeting_controller.settings_manager \
            if hasattr(self.timer_controller, 'meeting_controller') else SettingsManager()
        
        if not settings_manager.settings.display.show_predicted_end_time:
            # Hide label if it exists
            if self.end_time_label:
                self.end_time_label.setVisible(False)
            return
        
        # Create label if it doesn't exist
        if not self.end_time_label:
            self.end_time_label = QLabel()
            self.end_time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.end_time_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
            self.status_frame.layout().insertWidget(0, self.end_time_label)
        
        # Format the times
        original_time_str = original_end_time.strftime("%H:%M")
        predicted_time_str = predicted_end_time.strftime("%H:%M")
        
        # Calculate the difference
        time_diff = predicted_end_time - original_end_time
        diff_minutes = int(time_diff.total_seconds() / 60)
        
        # Set the text and color based on whether we're running over or under
        if diff_minutes > 0:
            # Running over time
            self.end_time_label.setText(f"Predicted End: {predicted_time_str} (+{diff_minutes} min)")
            self.end_time_label.setStyleSheet("""
                color: white; 
                background-color: rgba(255, 0, 0, 0.7);
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 24px;
                font-weight: bold;
            """)
        elif diff_minutes < 0:
            # Running under time
            self.end_time_label.setText(f"Predicted End: {predicted_time_str} ({diff_minutes} min)")
            self.end_time_label.setStyleSheet("""
                color: white; 
                background-color: rgba(0, 128, 0, 0.7);
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 24px;
                font-weight: bold;
            """)
        else:
            # On time
            self.end_time_label.setText(f"Predicted End: {predicted_time_str} (on time)")
            self.end_time_label.setStyleSheet("""
                color: white; 
                background-color: rgba(0, 0, 0, 0.7);
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 24px;
                font-weight: bold;
            """)
        
        # Make the label visible
        self.end_time_label.setVisible(True)
    
    def _meeting_ended(self):
        """Handle meeting end"""
        # Clear any overtime or end time displays
        if self.overtime_label:
            self.overtime_label.setVisible(False)
            
        if self.end_time_label:
            self.end_time_label.setVisible(False)
            
        # Show meeting completed message
        self.current_part_label.setText("Meeting Completed")
        self.presenter_label.setText("")
        self.presenter_label.setVisible(False)
    
    def show(self):
        """Override show to always show in fullscreen"""
        self.showFullScreen()