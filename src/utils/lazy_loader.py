"""
Lazy loading of components in the application to improve startup time and responsiveness.
This module provides a background thread to load components asynchronously, allowing the main UI to remain responsive.
It also includes a manager class to handle the loading process and caching of components.
The LazyComponentLoader class is responsible for loading components in a separate thread, emitting signals when components are loaded.
The ComponentLoadManager class manages the loading process, allowing components to be requested and providing signals when components are ready.
The SecondaryDisplayHandler class is responsible for managing the secondary display, including creating it on demand and applying the appropriate styling.
This module is designed to be used in a PyQt6 application, and it includes optimizations for loading components only when needed.
"""

from PyQt6.QtCore import QThread, pyqtSignal, QObject, QEventLoop, QTimer


class LazyComponentLoader(QThread):
    """Thread to load components asynchronously with improved signaling"""
    component_loaded = pyqtSignal(str, object)  # component_name, component_object
    all_components_loaded = pyqtSignal()
    progress_updated = pyqtSignal(str, int)  # component_name, progress percentage

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.components_to_load = [
            "meeting_view",
            "network_manager",
            "secondary_display"
        ]
        self.loaded_components = set()
        self.running = True
        self.priority_components = set()  # Components that should load first

    def run(self):
        """Load all heavy components in background with proper signaling"""
        try:
            # First load high-priority components if any are set
            for component in self.priority_components:
                if component == "meeting_view":
                    self._load_meeting_view()
                    self.progress_updated.emit("meeting_view", 33)
                elif component == "network_manager":
                    self._load_network_components()
                    self.progress_updated.emit("network_manager", 66)
                elif component == "secondary_display":
                    self._prepare_secondary_display()
                    self.progress_updated.emit("secondary_display", 100)

            # Now load any remaining components
            load_funcs = {
                "meeting_view": self._load_meeting_view,
                "network_manager": self._load_network_components,
                "secondary_display": self._prepare_secondary_display
            }
            
            to_load = [c for c in self.components_to_load if c not in self.loaded_components]
            total = len(to_load)
            
            for i, component in enumerate(to_load):
                if not self.running:
                    break
                if component in load_funcs:
                    load_funcs[component]()
                    progress = int(((i + 1) / total) * 100)
                    self.progress_updated.emit(component, progress)
        finally:
            if self.running:
                self.all_components_loaded.emit()

    def stop(self):
        """Stop the loading process"""
        self.running = False
        self.wait(1000)  # Wait up to 1 second for thread to finish
        if self.isRunning():
            self.terminate()
            
    def set_priority_components(self, components):
        """Set components that should be loaded first"""
        self.priority_components = set(components)

    def _load_meeting_view(self):
        """Load meeting view"""
        if "meeting_view" in self.loaded_components:
            return
            
        from src.views.meeting_view import MeetingView

        meeting_view = MeetingView(
            self.main_window.meeting_controller,
            self.main_window.timer_controller
        )
        self.component_loaded.emit("meeting_view", meeting_view)
        self.loaded_components.add("meeting_view")

    def _load_network_components(self):
        """Load network components"""
        if "network_manager" in self.loaded_components:
            return
            
        # Use the optimized NetworkDisplayManager instead
        # which already implements lazy loading
        from src.utils.network_display_manager import NetworkDisplayManager
        from src.views.network_status_widget import NetworkStatusWidget

        network_manager = NetworkDisplayManager(
            self.main_window.timer_controller,
            self.main_window.settings_controller.settings_manager
        )
        network_widget = NetworkStatusWidget(network_manager)

        self.component_loaded.emit("network_manager", network_manager)
        self.component_loaded.emit("network_widget", network_widget)
        self.loaded_components.add("network_manager")
        self.loaded_components.add("network_widget")

    def _prepare_secondary_display(self):
        """Prepare secondary display handler"""
        if "secondary_display" in self.loaded_components:
            return
            
        # Create and initialize the SecondaryDisplayHandler
        from src.views.secondary_display import SecondaryDisplay
        from PyQt6.QtWidgets import QApplication
        
        # Instead of creating the secondary display directly,
        # prepare the handler which will create it when needed
        secondary_display_handler = SecondaryDisplayHandler(
            self.main_window.timer_controller,
            self.main_window.settings_controller,
            self.main_window
        )
        
        self.component_loaded.emit("secondary_display_handler", secondary_display_handler)
        self.loaded_components.add("secondary_display")
        self.loaded_components.add("secondary_display_handler")


class ComponentLoadManager(QObject):
    """Manager for lazy loading components with better UI responsiveness"""
    
    # Signals
    component_ready = pyqtSignal(str, object)  # component_name, component
    all_components_ready = pyqtSignal()
    
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.loader = None
        self.component_cache = {}
        
    def start_loading(self, priority_components=None):
        """Start loading components in background"""
        if self.loader and self.loader.isRunning():
            return
            
        self.loader = LazyComponentLoader(self.main_window)
        
        # Connect signals
        self.loader.component_loaded.connect(self._on_component_loaded)
        self.loader.all_components_loaded.connect(self._on_all_loaded)
        
        # Set priority components if specified
        if priority_components:
            self.loader.set_priority_components(priority_components)
        
        # Start the loader thread
        self.loader.start()
        
    def get_component(self, name, blocking=False, timeout=2000):
        """
        Get a component by name, optionally blocking until it's loaded
        
        Args:
            name: Component name
            blocking: If True, block until component is loaded
            timeout: Maximum time to wait in milliseconds (only if blocking)
            
        Returns:
            The component or None if not loaded and non-blocking
        """
        # Check if component is already loaded
        if name in self.component_cache:
            return self.component_cache[name]
            
        # If not blocking, return None
        if not blocking:
            # Ensure the loader is running
            if not self.loader or not self.loader.isRunning():
                self.start_loading([name])  # Start with this component as priority
            return None
            
        # For blocking mode, wait for the component
        if not self.loader or not self.loader.isRunning():
            self.start_loading([name])
            
        # Create a local event loop to wait for the component
        loop = QEventLoop()
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        
        # Set up a handler for when the component is loaded
        def check_component(loaded_name, component):
            if loaded_name == name:
                loop.quit()
                
        # Connect the signal
        self.loader.component_loaded.connect(check_component)
        
        # Start the timer and wait
        timer.start(timeout)
        
        # Already loaded check (one more time to avoid race condition)
        if name in self.component_cache:
            timer.stop()
            self.loader.component_loaded.disconnect(check_component)
            return self.component_cache[name]
            
        # Wait for the component or timeout
        loop.exec()
        
        # Clean up
        timer.stop()
        self.loader.component_loaded.disconnect(check_component)
        
        # Return the component if it was loaded
        return self.component_cache.get(name)
    
    def _on_component_loaded(self, name, component):
        """Handle a component being loaded"""
        # Cache the component
        self.component_cache[name] = component
        
        # Emit signal that component is ready
        self.component_ready.emit(name, component)
        
    def _on_all_loaded(self):
        """Handle all components being loaded"""
        self.all_components_ready.emit()


# SecondaryDisplayHandler implementation (to be imported by the improved lazy loader)
class SecondaryDisplayHandler(QObject):
    """Handler for the secondary display to defer creation until needed"""
    
    def __init__(self, timer_controller, settings_controller, parent=None):
        super().__init__(parent)
        self.timer_controller = timer_controller
        self.settings_controller = settings_controller
        self.parent = parent
        self._secondary_display = None
        self._initialized = False
    
    def toggle_display(self):
        """Toggle the secondary display on/off"""
        settings = self.settings_controller.get_settings()
        new_state = not settings.display.use_secondary_screen
        
        self.settings_controller.toggle_secondary_screen(new_state)
        self.update_display()
        self.settings_controller.save_settings()
    
    def update_display(self):
        """Update secondary display based on settings"""
        settings = self.settings_controller.get_settings()
        
        if settings.display.use_secondary_screen and settings.display.secondary_screen_index is not None:
            # Create secondary window if it doesn't exist
            if not self._secondary_display:
                self._create_secondary_display()
            
            # Apply proper styling to ensure visibility
            self._apply_theme()
            
            # Show and position on the correct screen
            self._position_display()
        elif self._secondary_display:
            # Hide the secondary display
            self._secondary_display.hide()
    
    def _create_secondary_display(self):
        """Create the secondary display on demand"""
        # Import here to avoid loading at startup
        from src.views.secondary_display import SecondaryDisplay
        
        self._secondary_display = SecondaryDisplay(
            self.timer_controller, 
            self.settings_controller,
            self.parent
        )
        
        # Connect countdown updated signal to secondary display
        self.timer_controller.timer.meeting_countdown_updated.connect(
            self._secondary_display._update_countdown
        )
        
        # After connecting, ensure secondary display receives the latest countdown
        if self.timer_controller.timer._target_meeting_time:
            self.timer_controller.timer._update_current_time()
            
        self._initialized = True
    
    def _apply_theme(self):
        """Apply high-contrast styling to the secondary display"""
        if not self._secondary_display:
            return
        
        # Always apply a black background with white text for maximum visibility
        self._secondary_display.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #000000;
                color: #ffffff;
            }
            
            QLabel {
                color: #ffffff;
                font-weight: bold;
            }
            
            QFrame {
                background-color: rgba(50, 50, 50, 180);
                border: 2px solid #ffffff;
                border-radius: 15px;
            }
        """)
        
        # Check for direct timer_label attribute in newer implementation
        if hasattr(self._secondary_display, 'timer_label'):
            self._secondary_display.timer_label.setStyleSheet("""
                color: #ffffff;
                font-size: 380px;
                font-weight: bold;
                font-family: 'Courier New', monospace;
            """)
    
    def _position_display(self):
        """Position the secondary display on the correct screen"""
        if not self._secondary_display:
            return
        
        # Import screen handler here to avoid early loading
        from src.utils.screen_handler import ScreenHandler
        from PyQt6.QtWidgets import QApplication
        
        settings = self.settings_controller.get_settings()
        screen = ScreenHandler.get_configured_screen(settings, is_primary=False)
        
        if screen:
            geometry = screen.geometry()
            self._secondary_display.setGeometry(geometry)
            self._secondary_display.show()
            
            # Delay fullscreen mode to ensure proper positioning
            QTimer.singleShot(200, lambda: self._make_fullscreen(screen))
    
    def _make_fullscreen(self, screen):
        """Helper to enter fullscreen after delay"""
        if not self._secondary_display:
            return
            
        # Move the window to the screen's top-left first
        self._secondary_display.move(screen.geometry().topLeft())
        
        # Explicitly set the screen for the window
        if hasattr(self._secondary_display, 'windowHandle'):
            self._secondary_display.windowHandle().setScreen(screen)
            
        # Now go fullscreen
        self._secondary_display.showFullScreen()
    
    def get_display(self):
        """Get the secondary display instance (creating if needed)"""
        if not self._secondary_display and self.settings_controller.get_settings().display.use_secondary_screen:
            self._create_secondary_display()
        return self._secondary_display
    
    def is_active(self):
        """Check if secondary display is active"""
        return self._secondary_display is not None and self._secondary_display.isVisible()
    
    def cleanup(self):
        """Clean up resources"""
        if self._secondary_display:
            self._secondary_display.close()
            self._secondary_display = None