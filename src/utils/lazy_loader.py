# Lazy loading of components for a PyQt application

from PyQt6.QtCore import QThread, pyqtSignal


class LazyComponentLoader(QThread):
    """Thread to load components asynchronously"""
    component_loaded = pyqtSignal(str, object)  # component_name, component_object
    all_components_loaded = pyqtSignal()

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.components_to_load = [
            "meeting_view",
            "network_manager",
            "secondary_display"
        ]
        self.loaded_components = set()

    def run(self):
        """Load all heavy components in background"""
        try:
            self._load_meeting_view()
            self._load_network_components()
            self._prepare_secondary_display()
        finally:
            self.all_components_loaded.emit()

    def _load_meeting_view(self):
        from src.views.meeting_view import MeetingView

        meeting_view = MeetingView(
            self.main_window.meeting_controller,
            self.main_window.timer_controller
        )
        self.component_loaded.emit("meeting_view", meeting_view)
        self.loaded_components.add("meeting_view")

    def _load_network_components(self):
        from src.utils.network_display_manager import NetworkDisplayManager
        from src.views.network_status_widget import NetworkStatusWidget

        network_manager = NetworkDisplayManager(
            self.main_window.timer_controller,
            self.main_window.settings_controller.settings_manager
        )
        network_widget = NetworkStatusWidget(network_manager)

        self.component_loaded.emit("network_manager", network_manager)
        self.component_loaded.emit("network_widget", network_widget)
        self.loaded_components.update(["network_manager", "network_widget"])

    def _prepare_secondary_display(self):
        self.loaded_components.add("secondary_display")
