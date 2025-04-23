"""
Secondary display window for the JW Meeting Timer.
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, 
    QSizePolicy, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPalette, QColor, QFont

from src.controllers.timer_controller import TimerController
from src.views.timer_view import TimerView
from src.models.timer import TimerState, TimerDisplayMode


class SecondaryDisplay(QMainWindow):
    """Secondary display window for the timer"""
    
    def __init__(self, timer_controller: TimerController):
        super().__init__(None, Qt.WindowType.Window)
        self.timer_controller = timer_controller
        
        # Setup UI
        self._setup_ui()
        
        # Connect signals
        self._connect_signals()
        
        # Set window flags for presentation display
        self.setWindowFlags(
            Qt.WindowType.Window | 
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
    
    def _setup_ui(self):
        """Setup the UI components"""
        self.setWindowTitle("JW Meeting Timer - Secondary Display")
        
        # Set black background
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        self.setPalette(palette)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        
        # Timer view - larger for visibility
        self.timer_view = TimerView(self.timer_controller)
        self.timer_view.setMinimumHeight(400)
        
        # Increase font sizes for secondary display
        font = QFont()
        font.setPointSize(18)
        self.timer_view.part_label.setFont(font)
        self.timer_view.part_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        
        # Part information
        self.part_frame = QFrame()
        self.part_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.part_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 30);
                border-radius: 10px;
                padding: 10px;
            }
        """)
        
        part_layout = QVBoxLayout(self.part_frame)
        
        self.current_part_label = QLabel("Current Part")
        self.current_part_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.current_part_label.setStyleSheet("color: white; font-size: 28px; font-weight: bold;")
        
        self.presenter_label = QLabel("")
        self.presenter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.presenter_label.setStyleSheet("color: white; font-size: 20px;")
        
        part_layout.addWidget(self.current_part_label)
        part_layout.addWidget(self.presenter_label)
        
        # Add components to main layout
        layout.addWidget(self.timer_view, 3)  # 3:1 ratio
        layout.addWidget(self.part_frame, 1)
        
        # Add ESC key to close shortcut
        self.escape_timer = QTimer(self)
        self.escape_timer.timeout.connect(self._check_escape_key)
        self.escape_timer.start(100)  # Check every 100ms
    
    def _connect_signals(self):
        """Connect controller signals"""
        self.timer_controller.part_changed.connect(self._part_changed)
    
    def _part_changed(self, part, index):
        """Handle part change"""
        self.current_part_label.setText(part.title)
        
        if part.presenter:
            self.presenter_label.setText(part.presenter)
        else:
            self.presenter_label.setText("")
    
    def _check_escape_key(self):
        """Check if ESC key is pressed to exit fullscreen"""
        from PyQt6.QtGui import QKeySequence
        from PyQt6.QtWidgets import QApplication
        
        # If ESC is pressed
        if QApplication.keyboardModifiers() & Qt.KeyboardModifier.Key_Escape:
            self.showNormal()  # Exit fullscreen
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)