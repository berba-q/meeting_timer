"""
Screen handling utilities for the OnTime Meeting Timer application.
"""
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QGuiApplication, QScreen


class ScreenHandler:
    """Helper class to manage screen selection and positioning"""
    
    @staticmethod
    def get_all_screens():
        """Get information about all available screens"""
        screens = []
        primary_screen = QApplication.primaryScreen()
        for i, screen in enumerate(QApplication.screens()):
            geometry = screen.geometry()
            screens.append({
                'index': i,
                'name': screen.name(),
                'width': geometry.width(),
                'height': geometry.height(),
                'primary': (screen == primary_screen),
            })
        return screens
    
    @staticmethod
    def get_screen_by_name(name):
        """Get a screen by its name (more reliable than index in some cases)"""
        for screen in QApplication.screens():
            if screen.name() == name:
                return screen
        return None
    
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
        primary_screen = QApplication.primaryScreen()
        screens = QApplication.screens()
        for i, screen in enumerate(screens):
            if screen == primary_screen:
                return i
        # If not found, try to match by object identity
        screens = QApplication.screens()
        if primary_screen in screens:
            return screens.index(primary_screen)
        # If no match, prefer non-primary if available
        for i, screen in enumerate(screens):
            if screen != QApplication.primaryScreen():
                return i
        return 0  # fallback to first screen if only one available
    
    @staticmethod
    def save_screen_selection(settings, primary_screen, secondary_screen):
        """Save screen selection with both index and name for robustness"""
        # Save primary screen
        settings.display.primary_screen_index = primary_screen['index']
        settings.display.primary_screen_name = primary_screen['name']
        
        # Save secondary screen
        settings.display.secondary_screen_index = secondary_screen['index']
        settings.display.secondary_screen_name = secondary_screen['name']
        
    @staticmethod
    def get_configured_screen(settings, is_primary=True):
        """Get the configured screen (tries by index first, then by name)"""
        screens = QApplication.screens()
        
        if is_primary:
            index = settings.display.primary_screen_index
            name = getattr(settings.display, 'primary_screen_name', '')
        else:
            index = settings.display.secondary_screen_index
            name = getattr(settings.display, 'secondary_screen_name', '')
        
        # Try by index first
        if index is not None and 0 <= index < len(screens):
            return screens[index]
        
        # If index fails, try by name
        if name:
            for screen in screens:
                if screen.name() == name:
                    return screen
        
        # If all else fails, return primary screen for primary, second screen for secondary
        if is_primary:
            return QApplication.primaryScreen()
        else:
            # For secondary, use a non-primary screen if available
            primary_screen = QApplication.primaryScreen()
            secondary_candidates = [screen for screen in screens if screen != primary_screen]
            if secondary_candidates:
                return secondary_candidates[0]
            # Fallback to last available screen if present
            if screens:
                return screens[-1]
            return None