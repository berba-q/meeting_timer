"""
Screen handling utilities for the JW Meeting Timer application.
"""
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QGuiApplication, QScreen


class ScreenHandler:
    """Helper class to manage screen selection and positioning"""
    
    @staticmethod
    def get_all_screens():
        """Get information about all available screens"""
        screens = []
        for i, screen in enumerate(QApplication.screens()):
            geometry = screen.geometry()
            screens.append({
                'index': i,
                'name': screen.name(),
                'width': geometry.width(),
                'height': geometry.height(),
                'primary': screen.isPrimary()
            })
        return screens
    
    @staticmethod
    def get_screen_by_index(index):
        """Get a screen by its index"""
        screens = QApplication.screens()
        if 0 <= index < len(screens):
            return screens[index]
        return None
    
    @staticmethod
    def get_primary_screen_index():
        """Get the index of the system's primary screen"""
        screens = QApplication.screens()
        for i, screen in enumerate(screens):
            if screen.isPrimary():
                return i
        return 0  # Default to first screen if no primary found