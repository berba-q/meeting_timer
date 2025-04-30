from unittest.mock import MagicMock
import pytest
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt, QTimer

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.timer import TimerDisplayMode
from src.views.timer_view import TimerView
from src.controllers.timer_controller import TimerController

# Fixture to create QApplication
@pytest.fixture
def app():
    app = QApplication([])
    yield app
    app.quit()

def test_timer_view_display(app):
    # Create a timer controller with a mocked timer
    controller = TimerController()
    controller.timer._timer = MagicMock()
    
    # Create the view
    view = TimerView(controller)
    
    # Test that the view starts in digital mode
    assert view.display_mode == TimerDisplayMode.DIGITAL
    
    # Test switching to analog mode
    view.set_display_mode(TimerDisplayMode.ANALOG)
    assert view.display_mode == TimerDisplayMode.ANALOG
    assert hasattr(view, 'analog_clock')