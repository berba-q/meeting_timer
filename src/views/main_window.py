"""
Main application window for the OnTime meeting timer app.
"""
import os
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QTabWidget, QMessageBox, QDockWidget,
    QSplitter, QFrame, QToolBar, QStatusBar, QMenuBar,
    QApplication, QSizePolicy
)
from PyQt6.QtGui import QIcon, QAction, QFont
from PyQt6.QtCore import Qt, QSize, pyqtSlot, QTimer, QEvent, QThread, pyqtSignal, QObject
from PyQt6.QtWidgets import QDialog

from src.utils.screen_handler import ScreenHandler
from src.controllers.meeting_controller import MeetingController
from src.controllers.timer_controller import TimerController
from src.controllers.settings_controller import SettingsController
from src.models.settings import SettingsManager, TimerDisplayMode, MeetingSourceMode
from src.models.meeting import Meeting, MeetingType
from src.models.timer import TimerState
from src.views.timer_view import TimerView
from src.views.meeting_view import MeetingView
from src.views.settings_view import SettingsDialog
from src.views.secondary_display import SecondaryDisplay
from src.views.weekend_song_editor import WeekendSongEditorDialog
from src.utils.network_display_manager import NetworkDisplayManager
from src.utils.network_broadcaster import NetworkBroadcaster
from src.views.network_status_widget import NetworkStatusWidget, NetworkInfoDialog
from src.models.settings import NetworkDisplayMode
from src.utils.update_checker import check_for_updates


class UpdateCheckWorker(QObject):
    """Worker class for running update checks in a separate thread"""
    finished = pyqtSignal()
    
    def __init__(self, silent=False):
        super().__init__()
        self.silent = silent
        self._last_network_url = None
    
    def run(self):
        """Run the update check"""
        try:
            # Get the main window reference
            from PyQt6.QtWidgets import QApplication
            main_window = QApplication.activeWindow()
            
            # Import the update checker
            from src.utils.update_checker import check_for_updates
            
            # Run check on this thread
            check_for_updates(main_window, self.silent)
        except Exception as e:
            print(f"Error checking for updates: {e}")
        finally:
            self.finished.emit()

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self, meeting_controller: MeetingController, settings_controller: SettingsController):
        super().__init__()
        
        # Cache the last network URL so late‑loaded widgets can sync
        self._last_network_url = None
        
        # Initialize controllers
        self.meeting_controller = meeting_controller
        self.settings_controller = settings_controller
        self.timer_controller = TimerController(settings_controller)
        
        # Create the component load manager
        from src.utils.lazy_loader import ComponentLoadManager
        self.component_loader = ComponentLoadManager(self)
        
        # Connect component loader signals
        self.component_loader.component_ready.connect(self._on_component_ready)
        self.component_loader.all_components_ready.connect(self._on_all_components_ready)
        
        # Create placeholders for lazy-loaded components
        self.meeting_view = None
        self.network_display_manager = None
        self.network_status_widget = None
        self.secondary_display_handler = None
        # Secondary display window placeholder
        self.secondary_display = None
        
        # Setup UI
        self.setWindowTitle("OnTime Meeting Timer")
        self.setMinimumSize(600, 400)
        
        # Apply minimal styling immediately
        self._apply_minimal_styling()
        
        # Create tools dock first (before menu bar)
        self._create_empty_dock()
        
        # Show/hide the tools dock based on settings
        settings = self.settings_controller.get_settings()
        if settings.display.remember_tools_dock_state and settings.display.show_tools_dock:
            self.tools_dock.show()
        else:
            self.tools_dock.hide()
        
        # Now create other UI components
        self._create_menu_bar()
        self._create_tool_bar()
        self._create_central_widget()
        self._create_status_bar()
        
        # Connect signals
        self._connect_signals()
        
        # Initialize timer to show current time
        self._initialize_timer_display()
        
        # Start loading components in background
        QTimer.singleShot(100, self._start_component_loading)

    def _restore_window_size(self):
        self.setMinimumSize(600, 400)
        self.resize(600, 400)
        
    def _apply_minimal_styling(self):
        """Apply minimal styling for fast initial display"""
        theme = self.settings_controller.get_settings().display.theme
        if theme == "dark":
            self.setStyleSheet("""
                QMainWindow, QWidget {
                    background-color: #2d2d2d;
                    color: #f0f0f0;
                }
                QLabel {
                    color: #f0f0f0;
                }
                QPushButton {
                    background-color: #3d7ebd;
                    color: white;
                    border: 1px solid #2d6ebd;
                    padding: 5px;
                }
                QMessageBox QPushButton {
                    background-color: #3d7ebd;
                    color: white;
                    border: 1px solid #2d6ebd;
                    padding: 5px;
                    min-width: 80px;
                }
            """)
    
    def _create_empty_dock(self):
        """Create empty dock widgets for later population"""
        # Create tab widget for docked tools
        self.dock_tabs = QTabWidget()
        self.dock_tabs.setTabPosition(QTabWidget.TabPosition.North)
        
        # Create a placeholder widget
        placeholder = QWidget()
        placeholder_layout = QVBoxLayout(placeholder)
        loading_label = QLabel("Loading components...")
        placeholder_layout.addWidget(loading_label)
        
        # Add to dock tabs
        self.dock_tabs.addTab(placeholder, "Network")
        
        # Wrap in tools dock
        self.tools_dock = QDockWidget("Tools", self)
        self.tools_dock.setWidget(self.dock_tabs)
        self.tools_dock.setMinimumSize(200, 200)
        self.tools_dock.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.tools_dock.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetClosable)
        self.tools_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea | Qt.DockWidgetArea.LeftDockWidgetArea)
        
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.tools_dock)
        
        # Restore dock visibility state
        if self.settings_controller.get_settings().display.show_tools_dock:
            self.tools_dock.show()
        else:
            self.tools_dock.hide()
    
    def _start_component_loading(self):
        """Start loading components in background"""
        # Start with meeting_view as high priority
        self.component_loader.start_loading(priority_components=["meeting_view"])
        
        # Update status bar
        self.statusBar().showMessage("Loading components...", 5000)
    
    def _is_component_ready(self, component_name):
        """Check if a component is ready for use"""
        return hasattr(self, component_name) and getattr(self, component_name) is not None

    def _store_pending_action(self, component_name, method_name, *args, **kwargs):
        """Store a pending action to be executed when the component is ready"""
        if not hasattr(self, '_pending_actions'):
            self._pending_actions = {}
        
        if component_name not in self._pending_actions:
            self._pending_actions[component_name] = []
        
        self._pending_actions[component_name].append((method_name, args, kwargs))
        
        # If the component loader exists, try to prioritize loading this component
        if hasattr(self, 'component_loader') and self.component_loader:
            self.component_loader.start_loading(priority_components=[component_name])

    def _process_pending_actions(self, component_name, component):
        """Process any pending actions for a component that has just become available"""
        if not hasattr(self, '_pending_actions') or component_name not in self._pending_actions:
            return
        
        pending = self._pending_actions[component_name]
        for method_name, args, kwargs in pending:
            if hasattr(component, method_name):
                method = getattr(component, method_name)
                if callable(method):
                    method(*args, **kwargs)
        
        # Clear processed actions
        self._pending_actions[component_name] = []
        
    def _on_component_ready(self, name, component):
        """Handle a component being ready and process any pending actions"""
        # Store the component
        setattr(self, name, component)
        
        # Component-specific handling
        if name == "meeting_view":
            # Get the splitter from the central widget
            splitter = self.centralWidget().layout().itemAt(0).widget()

            # Get the second widget in the splitter (current placeholder)
            old_widget = splitter.widget(1)

            # Replace with the new meeting view
            splitter.replaceWidget(1, component)

            # Clean up the old widget
            if old_widget:
                old_widget.deleteLater()

            # Process any pending actions for this component
            self._process_pending_actions(name, component)

            # If we have a current meeting, update the view
            if self.meeting_controller.current_meeting:
                meeting = self.meeting_controller.current_meeting
                if meeting.meeting_type == MeetingType.WEEKEND:
                    meeting.title = f"Public Talk and Watchtower Study"
                component.set_meeting(meeting)
                
        elif name == "network_display_manager":
            self.network_display_manager = component
            # Connect the network manager's signals
            self._connect_network_display_signals()

            # connect the network signals to the network status widget
            self._connect_network_signals()

            # If the dock panel already exists, give it the manager reference
            if self.network_status_widget:
                self.network_status_widget.set_network_manager(self.network_display_manager)
                # Force sync with current state
                self._sync_network_widget_state()

            # Process any pending actions for this component
            self._process_pending_actions(name, component)
            
        elif name == "network_widget":
            # Replace the placeholder in the dock tabs
            old_widget = self.dock_tabs.widget(0)
            self.dock_tabs.removeTab(0)
            self.dock_tabs.insertTab(0, component, "Network")
            self.network_status_widget = component  # keep a reference

            # Hand over the manager reference (if it's already loaded)
            if self.network_display_manager:
                self.network_status_widget.set_network_manager(self.network_display_manager)
                # Force sync with current state
                self._sync_network_widget_state()
            else:
                self.network_status_widget._display_stopped()

            # Sync widget with current broadcast state
            if self._last_network_url:
                self.network_status_widget._display_started(self._last_network_url)
            else:
                self.network_status_widget._display_stopped()

            # Clean up the old widget
            if old_widget:
                old_widget.deleteLater()

            # Process any pending actions for this component
            self._process_pending_actions(name, component)
            # Sync widget with current broadcast state
            if self.network_display_manager and self.network_display_manager.broadcaster:
                if self.network_display_manager.broadcaster.is_broadcasting:
                    url, _, _ = self.network_display_manager.get_connection_info()
                    if url:
                        self.network_status_widget._display_started(url)
                else:
                    self.network_status_widget._display_stopped()
                
        elif name == "secondary_display_handler":
            # If secondary display is enabled, update it
            if self.settings_controller.get_settings().display.use_secondary_screen:
                QTimer.singleShot(1000, component.update_display)
                
            # Process any pending actions for this component
            self._process_pending_actions(name, component)
    
    def _sync_network_widget_state(self):
        """Explicitly synchronize the network widget with the actual network display state"""
        if not self.network_status_widget or not self.network_display_manager:
            return
            
        # Check if the network display is actually running
        if (self.network_display_manager.broadcaster and 
            self.network_display_manager.broadcaster.is_broadcasting):
            # Get the current connection URL
            url, client_count, _ = self.network_display_manager.get_connection_info()
            if url:
                # Force update the widget to active state
                self.network_status_widget._display_started(url)
                # Update status with client count
                self.network_status_widget._status_updated(
                    f"Network display running at: {url}",
                    client_count
                )
            else:
                # Fallback to inactive if no URL
                self.network_status_widget._display_stopped()
        else:
            # Ensure widget shows inactive state
            self.network_status_widget._display_stopped()
            
        # Update the toggle button text
        if hasattr(self.network_status_widget, "toggle_button"):
            if (self.network_display_manager.broadcaster and 
                self.network_display_manager.broadcaster.is_broadcasting):
                self.network_status_widget.toggle_button.setText("Stop")
            else:
                self.network_status_widget.toggle_button.setText("Start")

    
    def _on_all_components_ready(self):
        """Handle all components being loaded"""
        # Update status bar
        self.statusBar().showMessage("All components loaded", 3000)
        
        # Auto-start network display if enabled
        if self.settings_controller.get_settings().network_display.auto_start:
            mode = self.settings_controller.get_settings().network_display.mode
            if mode != NetworkDisplayMode.DISABLED and self.network_display_manager:
                QTimer.singleShot(500, self._auto_start_network_display)
                
    def _connect_network_display_signals(self):
        """Connect timer controller signals to network display manager after it's loaded"""
        if self.network_display_manager:
            print("Connecting network display manager signals")
            
            # Make sure the timer_controller is directly accessible
            self.network_display_manager.timer_controller = self.timer_controller
            
            # Connect timer signals to network display manager
            self.timer_controller.timer.time_updated.connect(self.network_display_manager._on_time_updated)
            self.timer_controller.timer.state_changed.connect(self.network_display_manager._on_state_changed)
            self.timer_controller.part_changed.connect(self.network_display_manager._on_part_changed)
            self.timer_controller.predicted_end_time_updated.connect(self.network_display_manager._on_predicted_end_time_updated)
            self.timer_controller.meeting_overtime.connect(self.network_display_manager._on_meeting_overtime)
            
            # Connect current time updates - use specific format for current time
            # This connects directly to the broadcaster
            self.timer_controller.timer.current_time_updated.connect(
                lambda time_str: self.network_display_manager._on_time_updated(
                    self.timer_controller.timer.remaining_seconds
                ) if self.network_display_manager else None
            )
            
            print("Network display manager signals connected successfully")
        else:
            print("WARNING: Cannot connect network display manager signals - component not loaded yet")
    
    def _check_for_updates(self, silent=False):
        """Check for application updates"""
        #from src.utils.update_checker import check_for_updates
        
        # Store the thread reference so it doesn't get garbage collected
        self.update_thread = check_for_updates(self, silent)
        
    
    def _show_update_dialog(self, version_info):
        """Show the update dialog (called from the main thread)"""
        from src.utils.update_checker import UpdateDialog
        dialog = UpdateDialog(version_info, self)
        dialog.exec()

    def _show_no_update_message(self):
        """Show no update available message (thread-safe)"""
        QTimer.singleShot(0, lambda: QMessageBox.information(
            self,
            "No Updates Available",
            "You are using the latest version of OnTime Meeting Timer."
        ))

    def _show_update_error(self, error_message):
        """Show update error message (thread-safe)"""
        QTimer.singleShot(0, lambda: QMessageBox.warning(
            self,
            "Update Check Failed",
            f"Failed to check for updates:\n{error_message}"
        ))
    
    def _initialize_timer_display(self):
        """Initialize timer to show current time and meeting countdown"""
        # Update the meeting selector with available meetings
        self._update_meeting_selector()
        
        # Auto-select the appropriate meeting based on current day
        self._auto_select_current_meeting()
        
        # If we have a current meeting, initialize the countdown
        if self.meeting_controller.current_meeting:
            meeting = self.meeting_controller.current_meeting
            self.timer_controller.set_meeting(meeting)
            
            # Force refresh of the meeting view
            if self._is_component_ready('meeting_view'):
                self.meeting_view.set_meeting(meeting)
            else:
                self._store_pending_action('meeting_view', 'set_meeting', meeting)
            
            # Ensure the status bar shows the correct meeting
            if meeting.meeting_type == MeetingType.WEEKEND:
                self.current_meeting_label.setText(f"Current Meeting: Public Talk and Watchtower Study ({meeting.date.strftime('%Y-%m-%d')})")
            else:
                self.current_meeting_label.setText(f"Current Meeting: {meeting.title}")
            
            # Debug output
            #print(f"Selected meeting in _initialize_timer_display: {meeting.title}, Type: {meeting.meeting_type.value}")
            #print(f"Sections: {[s.title for s in meeting.sections]}")
    
    def _auto_select_current_meeting(self):
        """Automatically select the appropriate meeting based on the current day"""
        if not self.meeting_controller.current_meetings:
            return
        
        # Get current date and settings
        now = datetime.now()
        current_day = now.weekday()  # 0 = Monday, 6 = Sunday
        settings = self.settings_controller.get_settings()
        
        # Get configured days from settings
        midweek_day = settings.midweek_meeting.day.value  # Day of week (0-6)
        weekend_day = settings.weekend_meeting.day.value  # Day of week (0-6)
        
        meeting_to_select = None
        selection_reason = ""
        
        # First check if today is either meeting day
        if current_day == midweek_day and MeetingType.MIDWEEK in self.meeting_controller.current_meetings:
            meeting_to_select = self.meeting_controller.current_meetings[MeetingType.MIDWEEK]
            selection_reason = f"Today is the midweek meeting day (day {current_day})"
        elif current_day == weekend_day and MeetingType.WEEKEND in self.meeting_controller.current_meetings:
            meeting_to_select = self.meeting_controller.current_meetings[MeetingType.WEEKEND]
            selection_reason = f"Today is the weekend meeting day (day {current_day})"
        else:
            # If today isn't a meeting day, find the next meeting day
            days_to_midweek = (midweek_day - current_day) % 7
            days_to_weekend = (weekend_day - current_day) % 7
            
            # Choose the closest upcoming meeting
            if days_to_midweek < days_to_weekend:
                if MeetingType.MIDWEEK in self.meeting_controller.current_meetings:
                    meeting_to_select = self.meeting_controller.current_meetings[MeetingType.MIDWEEK]
                    selection_reason = f"Midweek meeting is next (in {days_to_midweek} days)"
            else:
                if MeetingType.WEEKEND in self.meeting_controller.current_meetings:
                    meeting_to_select = self.meeting_controller.current_meetings[MeetingType.WEEKEND]
                    selection_reason = f"Weekend meeting is next (in {days_to_weekend} days)"
        
        # If we found a meeting to select, update the selector and set current meeting
        if meeting_to_select:
            print(f"Auto-selecting meeting: {selection_reason}")
            
            # Find the meeting in the selector
            found_index = -1
            for i in range(self.meeting_selector.count()):
                meeting = self.meeting_selector.itemData(i)
                if meeting and meeting.meeting_type == meeting_to_select.meeting_type:
                    found_index = i
                    break
            
            if found_index >= 0:
                # Temporarily block signals to avoid recursive updates
                self.meeting_selector.blockSignals(True)
                self.meeting_selector.setCurrentIndex(found_index)
                self.meeting_selector.blockSignals(False)
                
                # Update controllers and views
                self._set_current_meeting(meeting_to_select)
            else:
                print("Warning: Selected meeting not found in selector")
        else:
            print("No appropriate meeting found to auto-select")
            
    def _set_current_meeting(self, meeting):
        """Set the current meeting in all components safely"""
        if not meeting:
            return
        
        # Update the meeting controller
        self.meeting_controller.set_current_meeting(meeting)
        
        # Update the timer controller with the selected meeting
        self.timer_controller.set_meeting(meeting)
        
        # Update the meeting view
        if self._is_component_ready('meeting_view'):
            self.meeting_view.set_meeting(meeting)
        else:
            self._store_pending_action('meeting_view', 'set_meeting', meeting)
        
        # Update status bar
        if meeting.meeting_type == MeetingType.WEEKEND:
            self.current_meeting_label.setText(f"Current Meeting: Public Talk and Watchtower Study ({meeting.date.strftime('%Y-%m-%d')})")
        else:
            self.current_meeting_label.setText(f"Current Meeting: {meeting.title}")
        
        # Re‑enable countdown on the secondary display for the newly selected meeting
        if self.secondary_display:
            self.secondary_display.show_countdown = True
        # Initialize meeting countdown
        self.timer_controller._initialize_meeting_countdown()
        
        # Check for missing songs if this is a weekend meeting
        if meeting.meeting_type == MeetingType.WEEKEND:
            self._process_weekend_meeting_songs(meeting)
        #print(f"Current meeting set to: {meeting.title}, Type: {meeting.meeting_type.value}")
            
    def _update_countdown(self, seconds_remaining: int, message: str):
        """Update the countdown message with lazy-loaded components"""
        # Update status bar with countdown message
        if seconds_remaining > 0:
            # Show countdown in status bar
            self.current_part_label.setText(message)

            # If the secondary display exists *and* it is currently allowed to
            # show the countdown, update it as well.
            secondary_display = None
            if self._is_component_ready('secondary_display_handler'):
                secondary_display = self.secondary_display_handler.get_display()

            if secondary_display and getattr(secondary_display, "show_countdown", True):
                # Update the info label with just the countdown message
                try:
                    secondary_display = self.secondary_display_handler.get_display()
                    try:
                        if hasattr(secondary_display, "info_label1") and secondary_display.info_label1 is not None:
                            secondary_display.info_label1.setText(message)
                            secondary_display.info_label1.setStyleSheet("""
                                color: #4a90e2;
                                font-size: 80px;
                                font-weight: bold;
                            """)
                            # Clear the second label during countdown
                            secondary_display.info_label2.setText("")
                            # Set flag to track that we're currently showing the countdown
                            secondary_display.show_countdown = True
                    except RuntimeError as e:
                        print(f"Error updating secondary display: {e}")
                    except Exception as e:
                        print(f"Unexpected error updating secondary display: {e}")
                except Exception as e:
                    print(f"Error accessing secondary display: {e}")
                
        else:
            # Reset status bar when countdown ends
            # Disable further countdown updates on the secondary display until the
            # countdown is explicitly re‑enabled (e.g. for the next meeting).
            if self._is_component_ready('secondary_display_handler'):
                sd = self.secondary_display_handler.get_display()
                if sd:
                    sd.show_countdown = False
            if self.meeting_controller.current_meeting:
                meeting = self.meeting_controller.current_meeting
                if meeting.meeting_type == MeetingType.WEEKEND:
                    self.current_meeting_label.setText(f"Current Meeting: Public Talk and Watchtower Study ({meeting.date.strftime('%Y-%m-%d')})")
                else:
                    self.current_meeting_label.setText(f"Current Meeting: {meeting.title}")
            else:
                self.current_meeting_label.setText("No meeting selected")
    
    def _update_meeting_selector(self):
        """Update the meeting selector dropdown with available meetings"""
        self.meeting_selector.clear()
        
        meetings = self.meeting_controller.current_meetings
        if not meetings:
            self.meeting_selector.addItem("No meetings available")
            return
        
        # Avoid duplicate entries for the same meeting type
        seen_meeting_types = set()
        for meeting_type, meeting in meetings.items():
            if meeting_type in seen_meeting_types:
                continue
            seen_meeting_types.add(meeting_type)
            date_str = meeting.date.strftime("%Y-%m-%d")
            if meeting_type == MeetingType.WEEKEND:
                display_title = f"Public Talk and Watchtower Study ({date_str})"
            else:
                display_title = f"{meeting.title} ({date_str})"
            self.meeting_selector.addItem(display_title, meeting)
        
        # Select the first item
        if self.meeting_selector.count() > 0:
            self.meeting_selector.setCurrentIndex(0)
        
    def _show_secondary_display(self):
        """Show the secondary display on the configured screen"""
        
        settings = self.settings_controller.get_settings()

        # Create secondary window if it doesn't exist
        if not self.secondary_display:
            
            self.secondary_display = SecondaryDisplay(self.timer_controller, self.settings_controller, parent=self)
            #print("[DEBUG] SecondaryDisplay created")
            # Connect countdown updated signal to secondary display
            self.timer_controller.timer.meeting_countdown_updated.connect(
                self.secondary_display._update_countdown
            )
            #print("[DEBUG] Connected countdown signal to SecondaryDisplay._update_countdown")
            # After connecting, ensure secondary display receives the latest countdown
            if self.timer_controller.timer._target_meeting_time:
                #print("[DEBUG] Manually triggering countdown update for secondary display")
                self.timer_controller.timer._update_current_time()
            # Apply styling to ensure visibility
            self._apply_secondary_display_theme()

        # Use our ScreenHandler to position the window on the correct screen
        screen = ScreenHandler.get_configured_screen(settings, is_primary=False)
        if screen:
            self.secondary_display.setGeometry(screen.geometry())
            self.secondary_display.show()
            #print(f"[Pre-FullScreen] Secondary screen: {self.secondary_display.screen().name()}")
            QTimer.singleShot(1000, self._make_secondary_fullscreen)

        # Update status bar indicator
        self.secondary_display_label.setText("Secondary Display: Active")

        # Update toggle action state
        self.toggle_secondary_action.setChecked(True)

    def _make_secondary_fullscreen(self):
        """Helper to enter fullscreen after delay"""
        if self.secondary_display:
            #from PyQt6.QtWidgets import QApplication
            settings = self.settings_controller.get_settings()
            #print(f"[CHECK] screen index at fullscreen call: {settings.display.secondary_screen_index}")
            screen = ScreenHandler.get_configured_screen(settings, is_primary=False)

            if screen:
                #print(f"[Fullscreen Fix] Binding secondary window to screen: {screen.name()}")
                self.secondary_display.move(screen.geometry().topLeft())  # Explicitly move the window
                self.secondary_display.windowHandle().setScreen(screen)

            self.secondary_display.showFullScreen()
            #print(f"[Post-FullScreen] Secondary screen: {self.secondary_display.screen().name()}")
        
    def showEvent(self, event):
        """Override show event to initialize screens when window is shown"""
        super().showEvent(event)
        
        # This is the right time to initialize screens, after the window is fully created
        # and about to become visible
        self._initialize_screens()
        
        # Auto-start network display if enabled in settings
        if self.settings_controller.get_settings().network_display.auto_start:
            mode = self.settings_controller.get_settings().network_display.mode
            if mode != NetworkDisplayMode.DISABLED:
                QTimer.singleShot(1000, self._auto_start_network_display)
        
        # check for updates after a short delay
        #QTimer.singleShot(3000, lambda: self._check_for_updates(False))
    
    def _create_menu_bar(self):
        """Create the application menu bar"""
        from src.utils.resources import get_icon
        
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("&File")
        
        # Create new meeting
        new_meeting_action = QAction(get_icon("clock"), "&New Meeting", self)
        new_meeting_action.setShortcut("Ctrl+N")
        new_meeting_action.triggered.connect(self._create_new_meeting)
        file_menu.addAction(new_meeting_action)
        
        # Open meeting
        open_meeting_action = QAction(get_icon("clock"), "&Open Meeting", self)
        open_meeting_action.setShortcut("Ctrl+O")
        open_meeting_action.triggered.connect(self._open_meeting)
        file_menu.addAction(open_meeting_action)
        
        # Edit current meeting
        edit_meeting_action = QAction(get_icon("edit"), "&Edit Current Meeting", self)
        edit_meeting_action.setShortcut("Ctrl+E")
        edit_meeting_action.triggered.connect(self._edit_current_meeting)
        file_menu.addAction(edit_meeting_action)
        edit_songs_action = QAction(get_icon("music"), "Edit Weekend &Songs", self)
        edit_songs_action.setShortcut("Ctrl+Shift+S")
        edit_songs_action.triggered.connect(self._edit_weekend_meeting_songs)
        file_menu.addAction(edit_songs_action)
        
        file_menu.addSeparator()
        
        # Update meetings from web
        update_meetings_action = QAction(get_icon("increase"), "&Update Meetings from Web", self)
        update_meetings_action.setShortcut("F5")
        update_meetings_action.triggered.connect(lambda: self._check_for_updates(False))
        file_menu.addAction(update_meetings_action)
        
        file_menu.addSeparator()
        
        # View menu
        view_menu = menu_bar.addMenu("&View")
        
        # Network display actions
        self.network_menu = view_menu.addMenu("&Network Display")

        # Toggle network dock widget
        toggle_network_dock_action = QAction("Show Network Panel", self)
        toggle_network_dock_action.setCheckable(True)
        toggle_network_dock_action.setChecked(self.tools_dock.isVisible())
        toggle_network_dock_action.triggered.connect(lambda checked: self.tools_dock.setVisible(checked))
        self.network_menu.addAction(toggle_network_dock_action)

        # Start/stop network display
        self.toggle_network_action = QAction("Start Network Display", self)
        self.toggle_network_action.triggered.connect(self._toggle_network_display)
        self.network_menu.addAction(self.toggle_network_action)

        # Show network info
        network_info_action = QAction("Network Display Info...", self)
        network_info_action.triggered.connect(self._show_network_info)
        self.network_menu.addAction(network_info_action)
        
        # Settings
        settings_action = QAction(get_icon("settings"), "&Settings", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._open_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        # Exit
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        
        # Toggle secondary display
        self.toggle_secondary_action = QAction("Toggle &Secondary Display", self)
        self.toggle_secondary_action.setShortcut("F10")
        self.toggle_secondary_action.triggered.connect(self._toggle_secondary_display)
        self.toggle_secondary_action.setCheckable(True)
        self.toggle_secondary_action.setChecked(
            self.settings_controller.get_settings().display.use_secondary_screen
        )
        view_menu.addAction(self.toggle_secondary_action)
        
        # Switch display mode
        """ 
        switch_display_mode_action = QAction("Switch Display &Mode", self)
        switch_display_mode_action.setShortcut("F9")
        switch_display_mode_action.triggered.connect(self._toggle_display_mode)
        view_menu.addAction(switch_display_mode_action) 
        """
        
        # Switch theme
        self.theme_menu = view_menu.addMenu("&Theme")
        
        # Light theme action
        self.light_theme_action = QAction("&Light Theme", self)
        self.light_theme_action.setCheckable(True)
        self.light_theme_action.triggered.connect(lambda: self._set_theme("light"))
        self.theme_menu.addAction(self.light_theme_action)
        
        # Dark theme action
        self.dark_theme_action = QAction("&Dark Theme", self)
        self.dark_theme_action.setCheckable(True)
        self.dark_theme_action.triggered.connect(lambda: self._set_theme("dark"))
        self.theme_menu.addAction(self.dark_theme_action)
        
        # Set initial theme selection
        current_theme = self.settings_controller.get_settings().display.theme
        if current_theme == "dark":
            self.dark_theme_action.setChecked(True)
        else:
            self.light_theme_action.setChecked(True)
        
        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        
        # About
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
        help_menu.addSeparator()
        
        # Check for updates
        check_updates_action = QAction("&Check for Updates", self)
        check_updates_action.triggered.connect(lambda: self._check_for_updates(False))
        help_menu.addAction(check_updates_action)
    
    def _create_tool_bar(self):
        """Create the main toolbar"""
        from src.utils.resources import get_icon
        
        tool_bar = QToolBar("Main Toolbar")
        tool_bar.setIconSize(QSize(32, 32))
        tool_bar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, tool_bar)
        
        # Timer controls
        self.start_button = QPushButton("Start Meeting")
        self.start_button.setIcon(get_icon("play"))
        self.start_button.setIconSize(QSize(24, 24))
        self.start_button.setObjectName("startButton")
        self.start_button.clicked.connect(self._start_meeting)
        tool_bar.addWidget(self.start_button)
        
        self.pause_resume_button = QPushButton("Pause")
        self.pause_resume_button.setIcon(get_icon("pause"))
        self.pause_resume_button.setIconSize(QSize(24, 24))
        self.pause_resume_button.setObjectName("pauseButton")
        self.pause_resume_button.clicked.connect(self._toggle_pause_resume)
        self.pause_resume_button.setEnabled(False)
        tool_bar.addWidget(self.pause_resume_button)
        
        tool_bar.addSeparator()
        
        # Part navigation
        self.prev_button = QPushButton("Previous")
        self.prev_button.setIcon(get_icon("previous"))
        self.prev_button.setIconSize(QSize(24, 24))
        self.prev_button.clicked.connect(self._previous_part)
        self.prev_button.setEnabled(False)
        tool_bar.addWidget(self.prev_button)
        
        self.next_button = QPushButton("Next")
        self.next_button.setIcon(get_icon("next"))
        self.next_button.setIconSize(QSize(24, 24))
        self.next_button.clicked.connect(self._next_part)
        self.next_button.setEnabled(False)
        tool_bar.addWidget(self.next_button)
        
        tool_bar.addSeparator()
        
        # Time adjustment
        self.decrease_button = QPushButton("-1 Minute")
        self.decrease_button.setIcon(get_icon("decrease"))
        self.decrease_button.setIconSize(QSize(24, 24))
        self.decrease_button.clicked.connect(lambda: self._adjust_time(-1))
        self.decrease_button.setEnabled(False)
        tool_bar.addWidget(self.decrease_button)
        
        self.increase_button = QPushButton("+1 Minute")
        self.increase_button.setIcon(get_icon("increase"))
        self.increase_button.setIconSize(QSize(24, 24))
        self.increase_button.clicked.connect(lambda: self._adjust_time(1))
        self.increase_button.setEnabled(False)
        tool_bar.addWidget(self.increase_button)
        
        tool_bar.addSeparator()
        
        # Meeting selector
        self.meeting_selector = QComboBox()
        self.meeting_selector.currentIndexChanged.connect(self._meeting_selected)
        self.current_meeting_label = QLabel("No meeting selected")
        #tool_bar.addWidget("Current Meeting:")
        tool_bar.addWidget(self.meeting_selector)
        
        # Settings button
        settings_button = QPushButton("")
        settings_button.setIcon(get_icon("settings"))
        settings_button.clicked.connect(self._open_settings)
        tool_bar.addWidget(settings_button)
        
    def _toggle_network_display(self):
        """Toggle network display on/off with lazy-loaded components"""
        if not self._is_component_ready('network_display_manager'):
            # Try to load the network manager component
            if hasattr(self, 'component_loader') and self.component_loader:
                # Load with blocking to ensure it's available
                self.component_loader.get_component('network_display_manager', blocking=True, timeout=5000)
            
            # Check again if it's available
            if not self._is_component_ready('network_display_manager'):
                self.statusBar().showMessage("Network display component not available", 3000)
                return
        
        # Now use the component
        if self.network_display_manager.broadcaster and self.network_display_manager.broadcaster.is_broadcasting:
            # Stop network display
            self.network_display_manager.stop_network_display()
            self.toggle_network_action.setText("Start Network Display")
        else:
            # Start network display with current settings
            mode = self.settings_controller.get_settings().network_display.mode
            http_port = self.settings_controller.get_settings().network_display.http_port
            ws_port = self.settings_controller.get_settings().network_display.ws_port

            # Show the tools dock if it's not visible
            if not self.tools_dock.isVisible():
                self.tools_dock.show()

            # Start network display
            if mode != NetworkDisplayMode.DISABLED:
                QTimer.singleShot(0, lambda: self.network_display_manager.start_network_display(mode, http_port, ws_port))
                self.toggle_network_action.setText("Stop Network Display")
            else:
                # Show message if network display is disabled in settings
                QTimer.singleShot(0, lambda: QMessageBox.information(
                    self,
                    "Network Display Disabled",
                    "Network display is disabled in settings. Please enable it in Settings > Network Display."
                ))
    
    def _show_network_info(self):
        """Show network display information dialog with lazy-loaded components"""
        if not self._is_component_ready('network_display_manager'):
            # Try to load the network manager
            if hasattr(self, 'component_loader') and self.component_loader:
                # Load with blocking to ensure it's available
                self.component_loader.get_component('network_display_manager', blocking=True, timeout=5000)
            
            # Check again if it's available
            if not self._is_component_ready('network_display_manager'):
                self.statusBar().showMessage("Network display component not available", 3000)
                return
        
        # Now use the component
        from src.views.network_status_widget import NetworkInfoDialog
        dialog = NetworkInfoDialog(self.network_display_manager, self)
        dialog.exec()
        
    def _auto_start_network_display(self):
        """Auto-start network display with lazy-loaded components"""
        if not self._is_component_ready('network_display_manager'):
            # Try to load the network manager
            if hasattr(self, 'component_loader') and self.component_loader:
                # Store this as a pending action rather than blocking
                self._store_pending_action('network_display_manager', '_auto_start_network_display_impl')
                return
        
        # If we have the component, call the implementation
        self._auto_start_network_display_impl()
        
    def _auto_start_network_display_impl(self):
        """Implementation of auto-start network display once component is available"""
        if not self._is_component_ready('network_display_manager'):
            return
            
        mode = self.settings_controller.get_settings().network_display.mode
        http_port = self.settings_controller.get_settings().network_display.http_port
        ws_port = self.settings_controller.get_settings().network_display.ws_port
        
        # Start network display if enabled
        if mode != NetworkDisplayMode.DISABLED:
            self.network_display_manager.start_network_display(mode, http_port, ws_port)
            self.toggle_network_action.setText("Stop Network Display")
        
            # Also sync the network widget if it exists
            if self._is_component_ready('network_status_widget'):
                QTimer.singleShot(500, self._sync_network_widget_state)
    
    def _create_central_widget(self):
        """Create the central widget with timer and a placeholder for meeting view"""
        from PyQt6.QtWidgets import QProgressBar
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)
        
        # Splitter for timer and parts
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        
        # Timer view - this is needed right away so create it directly
        self.timer_view = TimerView(self.timer_controller)
        self.timer_view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        splitter.addWidget(self.timer_view)
        
        # Meeting view placeholder until the real one is loaded
        meeting_view_placeholder = QWidget()
        meeting_view_layout = QVBoxLayout(meeting_view_placeholder)
        
        # Create a placeholder message
        placeholder_label = QLabel("Loading meeting information...")
        placeholder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        meeting_view_layout.addWidget(placeholder_label)
        
        # Add progress indicator
        progress = QProgressBar()
        progress.setRange(0, 0)  # Indeterminate progress
        meeting_view_layout.addWidget(progress)
        
        meeting_view_placeholder.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        splitter.addWidget(meeting_view_placeholder)
        
        # Set initial sizes
        splitter.setSizes([300, 400])
        
        main_layout.addWidget(splitter)
        
        # Store splitter reference to allow replacing widgets later
        self.main_splitter = splitter
    
    def _create_status_bar(self):
        """Create the status bar"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # Current part label
        self.current_part_label = QLabel("No meeting selected")
        self.current_part_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        status_bar.addWidget(self.current_part_label)
        
        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Preferred
        )
        status_bar.addWidget(spacer)
        
        # Predicted end time label
        self.predicted_end_time_label = QLabel()
        self.predicted_end_time_label.setVisible(False)
        status_bar.addPermanentWidget(self.predicted_end_time_label)
        
        # Meeting overtime indicator
        self.meeting_overtime_label = QLabel()
        self.meeting_overtime_label.setVisible(False)
        status_bar.addPermanentWidget(self.meeting_overtime_label)
        
        # Display mode indicator
        """
        self.display_mode_label = QLabel()
        self._update_display_mode_label()
        status_bar.addPermanentWidget(self.display_mode_label)
        """
        
        # Secondary display indicator
        self.secondary_display_label = QLabel()
        self._update_secondary_display_label()
        status_bar.addPermanentWidget(self.secondary_display_label)
    
    def _connect_signals(self):
        """Connect controller signals to UI handlers"""
        # Meeting controller signals
        self.meeting_controller.meetings_loaded.connect(self._meetings_loaded)
        self.meeting_controller.meeting_updated.connect(self._meeting_updated)
        self.meeting_controller.error_occurred.connect(self._show_error)
        self.meeting_controller.part_updated.connect(self._part_updated)
        
        # Timer controller signals
        self.timer_controller.part_changed.connect(self._part_changed)
        self.timer_controller.meeting_started.connect(self._meeting_started)
        self.timer_controller.meeting_ended.connect(self._meeting_ended)
        self.timer_controller.transition_started.connect(self._transition_started)
        self.timer_controller.meeting_overtime.connect(self._meeting_overtime)
        self.timer_controller.predicted_end_time_updated.connect(self._update_predicted_end_time)
        self.timer_controller.timer.meeting_countdown_updated.connect(self._update_countdown)
        #print("[DEBUG] Connected timer countdown signal to MainWindow._update_countdown")
        
        # Settings controller signals
        self.settings_controller.settings_changed.connect(self._settings_changed)
        #self.settings_controller.display_mode_changed.connect(self._display_mode_changed)
        self.settings_controller.theme_changed.connect(self._theme_changed)

        # Connect settings_controller signal for secondary screen live change
        self.settings_controller.secondary_screen_changed.connect(self._on_secondary_screen_changed)
        
    def _connect_network_signals(self):
        """Connect network display manager signals when component is available"""
        if not hasattr(self, 'network_display_manager') or not self.network_display_manager:
            return
            
        # Connect network display manager signals
        self.network_display_manager.display_started.connect(self._network_display_started)
        self.network_display_manager.display_stopped.connect(self._network_display_stopped)

    
    def _network_display_started(self, url):
        """Handle network display started"""
        self._last_network_url = url # Store the URL for later use
        # Update menu action text
        self.toggle_network_action.setText("Stop Network Display")
        
        # Update status bar
        self.statusBar().showMessage(f"Network display started at {url}", 5000)
        if hasattr(self, "network_status_widget") and self.network_status_widget:
            self.network_status_widget._display_started(url)
        
        # network_status_widget is not None
        if self.network_status_widget:
            self.network_status_widget._display_started(url)
            
        # Update the network widget if it exists
        if hasattr(self, "network_status_widget") and self.network_status_widget:
            self.network_status_widget._display_started(url)
            # Make sure the toggle button text is updated too
            if hasattr(self.network_status_widget, "toggle_button"):
                self.network_status_widget.toggle_button.setText("Stop")

    def _network_display_stopped(self):
        """Handle network display stopped"""
        self._last_network_url = None # Clear the URL
        # Update menu action text
        self.toggle_network_action.setText("Start Network Display")
        
        # Update status bar
        self.statusBar().showMessage("Network display stopped", 5000)
        if hasattr(self, "network_status_widget") and self.network_status_widget:
            self.network_status_widget._display_stopped()
            # Make sure the toggle button text is updated too
            if hasattr(self.network_status_widget, "toggle_button"):
                self.network_status_widget.toggle_button.setText("Start")

    def _meetings_loaded(self, meetings):
        """Handle loaded meetings"""
        # Check for missing songs in weekend meeting
        if MeetingType.WEEKEND in meetings:
            print(">>> Weekend meeting found. Checking songs...")
            weekend_meeting = meetings[MeetingType.WEEKEND]
            self._process_weekend_meeting_songs(weekend_meeting)

        # Update meeting selector
        self.meeting_selector.clear()
        
        if not meetings:
            self.meeting_selector.addItem("No meetings available")
            return
        
        for meeting_type, meeting in meetings.items():
            date_str = meeting.date.strftime("%Y-%m-%d")
            if meeting_type == MeetingType.WEEKEND:
                display_title = f"Public Talk and Watchtower Study ({date_str})"
            else:
                display_title = f"{meeting.title} ({date_str})"
            self.meeting_selector.addItem(display_title, meeting)
    
    def _meeting_selected(self, index):
        """Handle meeting selection from the dropdown"""
        if index < 0 or self.meeting_selector.count() == 0:
            return
        
        meeting = self.meeting_selector.itemData(index)
        if meeting:
            self._set_current_meeting(meeting)

    
    def _meeting_updated(self, meeting):
        """Handle meeting update with lazy-loaded components"""
        if self._is_component_ready('meeting_view'):
            self.meeting_view.set_meeting(meeting)
        else:
            self._store_pending_action('meeting_view', 'set_meeting', meeting)

    
    def _part_changed(self, part, index):
        """Handle part change with lazy-loaded components"""
        # Update status bar
        self.current_part_label.setText(f"Current part: {part.title} ({part.duration_minutes} min)")

        # Highlight the current part in the meeting view
        if self._is_component_ready('meeting_view'):
            self.meeting_view.highlight_part(index)
        else:
            self._store_pending_action('meeting_view', 'highlight_part', index)

        # Display part information in the central widget
        self.timer_view.part_label.setText(f"{part.title} ({part.duration_minutes} min)")

        # Update secondary display if available
        if self._is_component_ready('secondary_display_handler'):
            secondary_display = self.secondary_display_handler.get_display()
            if secondary_display:
                # Check if there's a next part
                parts = self.timer_controller.parts_list
                if index + 1 < len(parts):
                    next_part = parts[index + 1]
                    # Update info_label1 with next part info
                    secondary_display.info_label1.setText(f"Next Part: {next_part.title}")
                    secondary_display.info_label1.setStyleSheet("""
                        color: #ffffff; 
                        font-size: 60px;
                        font-weight: bold;
                    """)
                else:
                    # No next part (this is the last part)
                    secondary_display.info_label1.setText("Last Part")
                    secondary_display.info_label1.setStyleSheet("""
                        color: #ffffff; 
                        font-size: 60px;
                        font-weight: bold;
                    """)
        
    def _part_updated(self, part, section_index, part_index):
        """Handle a part being updated"""
        global_index = self._get_global_part_index(section_index, part_index)

        # Replace the part in the timer's active list
        if 0 <= global_index < len(self.timer_controller.parts_list):
            self.timer_controller.parts_list[global_index] = part

            # If this is the current part and the timer is running, update its duration
            if global_index == self.timer_controller.current_part_index:
                self.timer_controller.apply_current_part_update()

        # Emit part_changed to refresh display
        self.timer_controller.part_changed.emit(part, global_index)
    
    def _meeting_started(self):
        """Handle meeting start event in the main window"""
        from src.utils.resources import get_icon
        
        self.start_button.setText("Stop Meeting")
        self.start_button.setIcon(get_icon("stop"))
        self.start_button.setObjectName("stopButton")  # Change style
        self.start_button.setStyleSheet("")  # Force style refresh
        self.start_button.clicked.disconnect()
        self.start_button.clicked.connect(self._stop_meeting)

        # Enable controls
        self.pause_resume_button.setEnabled(True)
        self.prev_button.setEnabled(True)
        self.next_button.setEnabled(True)
        self.decrease_button.setEnabled(True)
        self.increase_button.setEnabled(True)
        
        # If secondary display exists, update it to show meeting info
        self.timer_view.show_clock = False
        if self.secondary_display:
            self.secondary_display.show_clock = False
            # Hide countdown, show part info
            self.secondary_display.show_countdown = False
            
            # Set part information
            parts = self.timer_controller.parts_list
            if len(parts) > 1:
                # Show current and next part info
                self.secondary_display.info_label1.setText(f"Next Part: {parts[1].title}")
                self.secondary_display.info_label1.setStyleSheet("""
                    color: #ffffff; 
                    font-size: 60px;
                    font-weight: bold;
                """)
            else:
                # Only one part in the meeting
                self.secondary_display.info_label1.setText("Last Part")
                
            # Ensure both labels are visible
            self.secondary_display.info_label2.setVisible(True)
    
    def _meeting_ended(self):
        """Handle meeting end"""
        from src.utils.resources import get_icon
        
        self.start_button.setText("Start Meeting")
        self.start_button.setIcon(get_icon("play"))
        self.start_button.setObjectName("startButton")  # Change style
        self.start_button.setStyleSheet("")  # Force style refresh
        self.start_button.clicked.disconnect()
        self.start_button.clicked.connect(self._start_meeting)
        
        # Disable controls
        self.pause_resume_button.setEnabled(False)
        self.prev_button.setEnabled(False)
        self.next_button.setEnabled(False)
        self.decrease_button.setEnabled(False)
        self.increase_button.setEnabled(False)
        
        # Reset pause/resume button
        self.pause_resume_button.setText("Pause")
        self.pause_resume_button.setIcon(get_icon("pause"))
        self.pause_resume_button.setObjectName("pauseButton")  # Change style
        self.pause_resume_button.setStyleSheet("")  # Force style refresh
        
        # Reset overtime indicator
        self.meeting_overtime_label.setVisible(False)
        
        # Reset predicted end time
        self.predicted_end_time_label.setVisible(False)
        
        # show the clock in the timer view
        self.timer_view.show_clock = True
        
        # Update secondary display
        if self.secondary_display:
            self.secondary_display.show_clock = True
            # Show meeting completed message
            self.secondary_display.info_label1.setText("Meeting Completed")
            self.secondary_display.info_label1.setStyleSheet("""
                color: #ffffff; 
                font-size: 60px;
                font-weight: bold;
            """)
            # Clear predicted end time
            self.secondary_display.info_label2.setText("")
            # Reset countdown flag
            self.secondary_display.show_countdown = False
        # force an immediate refresh so the time appears right away
        self.timer_controller.timer._update_current_time()
    
    def _transition_started(self, transition_msg):
        """Handle chairman transition period"""
        # Update the current part label
        self.current_part_label.setText(f"⏳ {transition_msg} (1:00)")
        
        # Also update the part_label in the timer view
        self.timer_view.part_label.setText(transition_msg)
        
        # Update secondary display if available
        if self.secondary_display:
            # Use info_label1 instead of next_part_label in the new design
            self.secondary_display.info_label1.setText(transition_msg)
            self.secondary_display.info_label1.setStyleSheet("""
                color: #bb86fc; /* Purple for transitions */
                font-size: 60px;
                font-weight: bold;
            """)
    
    def _get_global_part_index(self, section_index, part_index):
        """Helper method to get global part index from section and part indices"""
        if not self.meeting_controller.current_meeting:
            return -1
        
        meeting = self.meeting_controller.current_meeting
        global_index = 0
        
        for i in range(section_index):
            global_index += len(meeting.sections[i].parts)
        
        global_index += part_index
        return global_index
    
    def _settings_changed(self):
        """Handle settings changes"""
        
        # Get current settings
        settings = self.settings_controller.get_settings()
        
        # Check if we need to force cleanup of the secondary display
        if settings.display.force_secondary_cleanup:
            # Clean up secondary display
            if hasattr(self, 'secondary_display') and self.secondary_display:
                self._cleanup_secondary_display()
                
            # Reset the flag
            settings.display.force_secondary_cleanup = False
            self.settings_controller.save_settings()
        # Defer UI updates to avoid potential widget destruction issues
        QTimer.singleShot(0, self._update_secondary_display_label)
        QTimer.singleShot(0, self._update_secondary_display)
        
        # Update tools dock visibility based on settings, but only if remember_tools_dock_state is true
        if settings.display.remember_tools_dock_state:
            QTimer.singleShot(0, lambda: self.tools_dock.setVisible(settings.display.show_tools_dock))
    
    """
    def _display_mode_changed(self, mode):
        self.timer_view.set_display_mode(mode)
        
        # Check if secondary display exists before trying to update it
        if self.secondary_display:
            # Check what attributes are available
            if hasattr(self.secondary_display, 'timer_view'):
                # Old implementation with timer_view
                self.secondary_display.timer_view.set_display_mode(mode)
            else:
                # New implementation with direct timer label
                # No need to change display mode as it's always digital
                pass
                
        self._update_display_mode_label()
    """
    """
    def _update_display_mode_label(self):
        mode = self.settings_controller.get_settings().display.display_mode
        mode_text = "Digital" if mode == TimerDisplayMode.DIGITAL else "Analog"
        self.display_mode_label.setText(f"Display Mode: {mode_text}")
    """
    
    def _update_secondary_display_label(self):
        """Update the secondary display indicator in the status bar"""
        settings = self.settings_controller.get_settings()
        if settings.display.use_secondary_screen and settings.display.secondary_screen_index is not None:
            self.secondary_display_label.setText("Secondary Display: Active")
        else:
            self.secondary_display_label.setText("Secondary Display: Inactive")
    
    def _apply_current_theme(self):
        """Apply the current theme from settings"""
        from src.utils.resources import apply_stylesheet
        
        theme = self.settings_controller.get_settings().display.theme
        apply_stylesheet(QApplication.instance(), theme)
    
    def _set_theme(self, theme: str):
        """Set the application theme"""
        # Update theme in settings
        self.settings_controller.set_theme(theme)
        
        # Update menu checkboxes
        self.light_theme_action.setChecked(theme == "light")
        self.dark_theme_action.setChecked(theme == "dark")
        
        # Apply the theme
        self._apply_current_theme()
    
    def _theme_changed(self, theme: str):
        """Handle theme change from settings"""
        # Update menu checkboxes
        self.light_theme_action.setChecked(theme == "light")
        self.dark_theme_action.setChecked(theme == "dark")
        
        # Apply the theme
        self._apply_current_theme()
        
        # Update secondary display if open
        if self.secondary_display:
            self._apply_secondary_display_theme()
    
    def _apply_secondary_display_theme(self):
        """Apply high-contrast styling to the secondary display regardless of theme"""
        if not self.secondary_display:
            return
        
        try:
            # Always apply a black background with white text for maximum visibility
            self.secondary_display.setStyleSheet("""
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
                
                TimerView {
                    background-color: #000000;
                    border: 2px solid #333333;
                }
                
                TimerView QLabel {
                    color: #ffffff;
                    font-weight: bold;
                }
            """)
            
            # Check if the attribute exists before trying to access it
            if hasattr(self.secondary_display, 'timer_view'):
                try:
                    if hasattr(self.secondary_display.timer_view, 'timer_label'):
                        self.secondary_display.timer_view.timer_label.setStyleSheet("color: #ffffff; font-weight: bold;")
                except (RuntimeError, AttributeError):
                    # Ignore errors if the component has been deleted
                    pass
            
            # Check for direct timer_label attribute in newer implementation
            if hasattr(self.secondary_display, 'timer_label'):
                try:
                    self.secondary_display.timer_label.setStyleSheet("""
                        color: #ffffff;
                        font-size: 380px;
                        font-weight: bold;
                        font-family: 'Courier New', monospace;
                    """)
                except (RuntimeError, AttributeError):
                    pass
        except Exception as e:
            print(f"Error applying secondary display theme: {e}")
    
    def _start_meeting(self):
        """Start the current meeting"""
        if not self.meeting_controller.current_meeting:
            QTimer.singleShot(0, lambda: QMessageBox.warning(self, "No Meeting Selected",
                                                            "Please select a meeting to start."))
            return

        self.timer_controller.start_meeting()
    
    def _stop_meeting(self):
        """Stop the current meeting"""
        self.timer_controller.stop_meeting()
    
    def _toggle_pause_resume(self):
        """Toggle between pause and resume"""
        from src.utils.resources import get_icon
        
        if self.timer_controller.timer.state == TimerState.RUNNING:
            self.timer_controller.pause_timer()
            self.pause_resume_button.setText("Resume")
            self.pause_resume_button.setIcon(get_icon("play"))
            self.pause_resume_button.setObjectName("startButton")  # Change style
            self.pause_resume_button.setStyleSheet("")  # Force style refresh
        else:
            self.timer_controller.resume_timer()
            self.pause_resume_button.setText("Pause")
            self.pause_resume_button.setIcon(get_icon("pause"))
            self.pause_resume_button.setObjectName("pauseButton")  # Change style
            self.pause_resume_button.setStyleSheet("")  # Force style refresh
    
    def _next_part(self):
        """Move to the next part"""
        self.timer_controller.next_part()
    
    def _previous_part(self):
        """Move to the previous part"""
        self.timer_controller.previous_part()
    
    def _adjust_time(self, minutes_delta):
        """Adjust timer by adding/removing minutes"""
        self.timer_controller.adjust_time(minutes_delta)
    
    def _create_new_meeting(self):
        """Create a new custom meeting"""
        # Show the meeting editor dialog
        self.meeting_controller.show_meeting_editor(self)
    
    def _open_meeting(self):
        """Open an existing meeting file"""
        from PyQt6.QtWidgets import QFileDialog

        # Show file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Meeting",
            str(self.meeting_controller.meetings_dir),
            "Meeting Files (*.json)"
        )

        if file_path:
            try:
                # Load meeting
                meeting = self.meeting_controller._load_meeting_file(file_path)
                if meeting:
                    # Set as current meeting
                    self.meeting_controller.set_current_meeting(meeting)

                    # Update meeting view
                    if self._is_component_ready('meeting_view'):
                        self.meeting_view.set_meeting(meeting)
                    else:
                        self._store_pending_action('meeting_view', 'set_meeting', meeting)

                    # Add to recent meetings
                    if file_path not in self.meeting_controller.settings_manager.settings.recent_meetings:
                        self.meeting_controller.settings_manager.settings.recent_meetings.append(file_path)
                        self.meeting_controller.settings_manager.save_settings()
            except Exception as e:
                QTimer.singleShot(0, lambda: QMessageBox.critical(self, "Error", f"Failed to load meeting: {str(e)}"))
    
    def _update_meetings(self):
        """Update meetings from web with enhanced weekend meeting handling"""
        # Check meeting source mode
        mode = self.settings_controller.get_settings().meeting_source.mode
        if mode == MeetingSourceMode.WEB_SCRAPING:
            # Show a progress dialog
            from PyQt6.QtWidgets import QProgressDialog
            progress = QProgressDialog("Updating meetings from wol.jw.org...", "Cancel", 0, 0, self)
            progress.setWindowTitle("Updating Meetings")
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.show()

            try:
                # Use web scraping
                meetings = self.meeting_controller.update_meetings_from_web()

                # Process weekend meeting to ensure songs are properly displayed
                if MeetingType.WEEKEND in meetings:
                    weekend_meeting = meetings[MeetingType.WEEKEND]
                    self._process_weekend_meeting_songs(weekend_meeting)

                progress.close()

                # Show a success message
                QTimer.singleShot(0, lambda: QMessageBox.information(self, "Update Complete",
                                               "Meetings have been successfully updated."))
            except Exception as e:
                progress.close()
                QTimer.singleShot(0, lambda: QMessageBox.warning(self, "Update Failed",
                                              f"Failed to update meetings: {str(e)}"))
        else:
            # Show options dialog as before
            from PyQt6.QtWidgets import QMenu

            menu = QMenu(self)
            web_action = menu.addAction("Update from Web")
            web_action.triggered.connect(self.meeting_controller.update_meetings_from_web)

            edit_action = menu.addAction("Edit Current Meeting")
            edit_action.triggered.connect(lambda: self._edit_current_meeting())

            menu.addSeparator()

            create_action = menu.addAction("Create New Meeting")
            create_action.triggered.connect(self._create_new_meeting)

            # Position menu below the update button
            menu.exec(self.sender().mapToGlobal(self.sender().rect().bottomLeft()))
            
    def _process_weekend_meeting_songs(self, meeting: Meeting):
        """Process weekend meeting to ensure songs are properly displayed"""
        print(f">>> [SongCheck] Meeting title: {meeting.title}, type: {meeting.meeting_type}")
        if meeting.meeting_type != MeetingType.WEEKEND:
            print(">>> Skipping song prompt — not a weekend meeting")
            return
        # Check for missing songs in the meeting
        import re
        missing_songs = False

        for section in meeting.sections:
            for part in section.parts:
                print(f"Part: {part.title}")
                title = part.title.lower().strip()
                if "song" in title and not re.search(r'song\s+\d+', title):
                    missing_songs = True

        if missing_songs:
            def ask_and_edit():
                from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QHBoxLayout, QPushButton
                from PyQt6.QtCore import Qt, QTimer
                print(">>> Showing custom song edit dialog")
                dialog = QDialog(self)
                dialog.setWindowTitle("Song Entry Required")
                dialog.setMinimumWidth(450)
                dialog.setModal(True)
                dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

                layout = QVBoxLayout(dialog)

                info_label = QLabel(
                    "<b>Some meeting songs are missing.</b><br><br>"
                    "Would you like to edit them now?"
                )
                info_label.setWordWrap(True)
                layout.addWidget(info_label)

                buttons_layout = QHBoxLayout()
                edit_now_button = QPushButton("Edit Now")
                edit_now_button.clicked.connect(lambda: dialog.accept())
                buttons_layout.addWidget(edit_now_button)

                skip_button = QPushButton("Skip")
                def handle_skip():
                    dialog.reject()
                    QTimer.singleShot(200, self._force_normal_window_state)
                skip_button.clicked.connect(handle_skip)
                buttons_layout.addWidget(skip_button)

                layout.addLayout(buttons_layout)

                if dialog.exec() == QDialog.DialogCode.Accepted:
                    from src.views.weekend_song_editor import WeekendSongEditorDialog
                    # Save window state before opening the editor dialog
                    was_maximized = self.isMaximized()
                    was_fullscreen = self.isFullScreen()

                    editor_dialog = WeekendSongEditorDialog(meeting, self)
                    if editor_dialog.exec() == QDialog.DialogCode.Accepted:
                        self.meeting_controller.save_meeting(meeting)
                        if self._is_component_ready('meeting_view'):
                            self.meeting_view.set_meeting(meeting)
                        else:
                            self._store_pending_action('meeting_view', 'set_meeting', meeting)

                    # Restore the window state after the dialog closes
                    if was_maximized:
                        self.showMaximized()
                    elif was_fullscreen:
                        self.showFullScreen()
                    else:
                        QTimer.singleShot(200, self._force_normal_window_state)
            QTimer.singleShot(0, ask_and_edit)

    def _force_normal_window_state(self):
        self.showNormal()

        # Only resize if the window is unusually large
        if self.width() > 1000 or self.height() > 800:
            self.resize(800, 600)

        # Center the window on the primary screen
        screen = QApplication.primaryScreen()
        if screen:
            screen_geometry = screen.availableGeometry()
            window_geometry = self.frameGeometry()
            window_geometry.moveCenter(screen_geometry.center())
            self.move(window_geometry.topLeft())
    
    def _edit_current_meeting(self):
        """Edit the currently selected meeting"""
        if not self.meeting_controller.current_meeting:
            QTimer.singleShot(0, lambda: QMessageBox.warning(self, "No Meeting Selected",
                                                            "Please select a meeting to edit."))
            return

        from src.views.meeting_editor_dialog import MeetingEditorDialog

        dialog = MeetingEditorDialog(self, self.meeting_controller.current_meeting)
        dialog.meeting_updated.connect(self._on_meeting_updated)
        dialog.exec()

        # Pass the _on_meeting_updated method so changes reflect live
        self.meeting_controller.show_meeting_editor(
        self,
        self.meeting_controller.current_meeting,
        self._on_meeting_updated
        )


    def _on_meeting_updated(self, updated_meeting: Meeting):
        """Apply updated meeting edits immediately"""
        self.meeting_controller.set_current_meeting(updated_meeting)
        self.timer_controller.set_meeting(updated_meeting)
        self._initialize_timer_display()
    
    def _edit_weekend_meeting_songs(self):
        """Edit weekend meeting songs"""
        current_meeting = self.meeting_controller.current_meeting

        # Check if we have a weekend meeting selected
        if not current_meeting or current_meeting.meeting_type != MeetingType.WEEKEND:
            QTimer.singleShot(0, lambda: QMessageBox.warning(self, "Not a Weekend Meeting",
                                                            "Please select a weekend meeting first."))
            return

        # Show the weekend song editor dialog
        from src.views.weekend_song_editor import WeekendSongEditorDialog
        dialog = WeekendSongEditorDialog(current_meeting, self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Save the updated meeting
            self.meeting_controller.save_meeting(current_meeting)

            # Update the meeting display
            if self._is_component_ready('meeting_view'):
                self.meeting_view.set_meeting(current_meeting)
            else:
                self._store_pending_action('meeting_view', 'set_meeting', current_meeting)

            # Show confirmation message
            QTimer.singleShot(0, lambda: QMessageBox.information(self, "Songs Updated",
                                                                "Weekend meeting songs have been updated."))
    
    def _open_settings(self):
        """Open settings dialog"""
        dialog = SettingsDialog(self.settings_controller, self)
        dialog.exec()
    
    def _initialize_screens(self):
        """Initialize screen handling during application startup"""
        # Get the current settings (reload from disk to ensure up-to-date)
        settings = self.settings_controller.settings_manager._load_settings()
        
        
        # Position main window on the primary screen
        self._position_main_window()
        
        # Show secondary display if enabled in settings
        if settings.display.use_secondary_screen:
            # Delay the creation of secondary display longer to ensure
            # the main window is fully displayed first and avoid focus hijack
            QTimer.singleShot(800, self._show_secondary_display)
            #("[Init] Delaying secondary display setup to avoid focus hijack")
    
    def _position_main_window(self):
        """Position the main window on the primary screen from settings"""
        settings = self.settings_controller.get_settings()
        #primary_index = settings.display.primary_screen_index
        
        # Get the screen by index
        screen = ScreenHandler.get_configured_screen(settings, is_primary=True)
        if screen:
            # Center the window on the selected primary screen
            geometry = screen.availableGeometry()
            self.setGeometry(
                geometry.x() + (geometry.width() - self.width()) // 2,
                geometry.y() + (geometry.height() - self.height()) // 2,
                self.width(),
                self.height()
            )
    
    def _toggle_secondary_display(self):
        """Toggle the secondary display window with lazy-loaded components"""
        if not self._is_component_ready('secondary_display_handler'):
            # Try to load the component
            if hasattr(self, 'component_loader') and self.component_loader:
                # Load with blocking to ensure it's available
                self.component_loader.get_component('secondary_display_handler', blocking=True, timeout=5000)
            
            # Check again if it's available
            if not self._is_component_ready('secondary_display_handler'):
                self.statusBar().showMessage("Secondary display component not available", 3000)
                return
        
        # Now use the component
        self.secondary_display_handler.toggle_display()
        
        # Update toggle action
        settings = self.settings_controller.get_settings()
        self.toggle_secondary_action.setChecked(settings.display.use_secondary_screen)
        
        # Update status label
        is_active = settings.display.use_secondary_screen
        self.secondary_display_label.setText(
            "Secondary Display: Active" if is_active else "Secondary Display: Inactive"
        )
    
    def _update_secondary_display(self):
        """Update secondary display based on settings"""
        try:
            settings = self.settings_controller.get_settings()
            
            if settings.display.use_secondary_screen and settings.display.secondary_screen_index is not None:
                # Create secondary window if it doesn't exist
                if not self.secondary_display:
                    self.secondary_display = SecondaryDisplay(self.timer_controller, self.settings_controller)
                
                if self.secondary_display:
                    # Apply proper styling to ensure visibility
                    self._apply_secondary_display_theme()

                    # Show and position on the correct screen
                    self.secondary_display.show()
                    self._position_secondary_display()

                # Update toggle action
                self.toggle_secondary_action.setChecked(True)
            elif hasattr(self, 'secondary_display') and self.secondary_display:
                # Hide the secondary display
                try:
                    self.secondary_display.hide()
                    # Update toggle action
                    self.toggle_secondary_action.setChecked(False)
                    # Clean up the secondary display to avoid resource leaks
                    self._cleanup_secondary_display()
                except Exception as e:
                    print(f"Error hiding secondary display: {e}")
                
        except Exception as e:
            print(f"Error updating secondary display: {e}")
    
    def _cleanup_secondary_display(self):
        """Safely clean up the secondary display window"""
        try:
            if hasattr(self, 'secondary_display') and self.secondary_display:
                # Disconnect any signals
                try:
                    self.timer_controller.timer.meeting_countdown_updated.disconnect(
                        self.secondary_display._update_countdown
                    )
                except (TypeError, RuntimeError):
                    # Signal might not be connected
                    pass
                
                # Delete the window
                self.secondary_display.deleteLater()
                self.secondary_display = None
        except Exception as e:
            print(f"Error cleaning up secondary display: {e}")
    
    def _position_secondary_display(self):
        """Position the secondary display on the correct screen"""
        if not hasattr(self, 'secondary_display') or not self.secondary_display:
            return
        
        try:
            settings = self.settings_controller.get_settings()
            screens = self.settings_controller.get_all_screens()
            
            if settings.display.secondary_screen_index is not None and 0 <= settings.display.secondary_screen_index < len(screens):
                screen = QApplication.screens()[settings.display.secondary_screen_index]
                geometry = screen.geometry()
                
                # Center on the selected screen
                self.secondary_display.setGeometry(geometry)
                self.secondary_display.showFullScreen()
                QTimer.singleShot(1000, self._make_secondary_fullscreen)
        except Exception as e:
            print(f"Error positioning secondary display: {e}")
    """  
    def _toggle_display_mode(self):
        settings = self.settings_controller.get_settings()
        current_mode = settings.display.display_mode
        
        if current_mode == TimerDisplayMode.DIGITAL:
            self.settings_controller.set_display_mode(TimerDisplayMode.ANALOG)
        else:
            self.settings_controller.set_display_mode(TimerDisplayMode.DIGITAL)
    """ 
    
    def _meeting_overtime(self, total_overtime_seconds):
        """Handle meeting overtime notification"""
        # Only show if there's actual overtime
        if total_overtime_seconds > 0:
            # Format the overtime
            minutes = total_overtime_seconds // 60
            seconds = total_overtime_seconds % 60
            
            # Update and show the label
            self.meeting_overtime_label.setText(f"Meeting Overtime: {minutes:02d}:{seconds:02d}")
            self.meeting_overtime_label.setStyleSheet("color: red; font-weight: bold;")
            self.meeting_overtime_label.setVisible(True)
    
    def _update_predicted_end_time(self, original_end_time, predicted_end_time):
        """Update the predicted end time display"""
        # Only show if the setting is enabled
        settings = self.settings_controller.get_settings()
        if not settings.display.show_predicted_end_time:
            self.predicted_end_time_label.setVisible(False)
            return
        
        # Format the times
        original_time_str = original_end_time.strftime("%H:%M")
        predicted_time_str = predicted_end_time.strftime("%H:%M")
        
        # Calculate the difference
        time_diff = predicted_end_time - original_end_time
        diff_minutes = int(time_diff.total_seconds() / 60)
        
        # Set the text and color based on whether we're running over or under
        if diff_minutes > 0:
            # Running over time
            self.predicted_end_time_label.setText(f"End: {predicted_time_str} (+{diff_minutes} min)")
            self.predicted_end_time_label.setStyleSheet("color: red;")
        elif diff_minutes < 0:
            # Running under time
            self.predicted_end_time_label.setText(f"End: {predicted_time_str} ({diff_minutes} min)")
            self.predicted_end_time_label.setStyleSheet("color: green;")
        else:
            # On time
            self.predicted_end_time_label.setText(f"End: {predicted_time_str} (on time)")
            self.predicted_end_time_label.setStyleSheet("color: black;")
        
        # Make the label visible
        self.predicted_end_time_label.setVisible(True)
    
    def _show_about(self):
        """Show the about dialog"""
        QMessageBox.about(
            self, 
            "About OnTime Meeting Timer",
            "OnTime Meeting Timer\n\n"
            "A cross-platform timer application for managing JW meeting schedules.\n\n"
            "© 2025 Open Source"
        )
    
    def _show_error(self, message):
        """Show error message (thread-safe)"""
        QTimer.singleShot(0, lambda: QMessageBox.critical(self, "Error", message))
        
    
    # ------------------------------------------------------------------
    # Ensure all child windows shut down cleanly when the main window
    # is closed (especially the secondary display, which otherwise keeps
    # running and may spawn duplicates next time).
    # ------------------------------------------------------------------
    def closeEvent(self, event):
        """Qt close handler – make sure secondary display and background
        tasks are cleaned up before the application quits."""
        try:
            # Shut down the secondary display if it exists
            if hasattr(self, "secondary_display") and self.secondary_display:
                # Disconnect signals to avoid callbacks during teardown
                try:
                    self.timer_controller.timer.meeting_countdown_updated.disconnect(
                        self.secondary_display._update_countdown
                    )
                except (TypeError, RuntimeError):
                    pass
                self.secondary_display.close()
                self.secondary_display.deleteLater()
                self.secondary_display = None
        except Exception as e:
            print(f"[MainWindow] Error while closing secondary display: {e}")

        # Also make sure the network display stops broadcasting
        if getattr(self, "network_display_manager", None):
            try:
                self.network_display_manager.stop_network_display()
            except Exception as e:
                print(f"[MainWindow] Error stopping network display: {e}")

        # Finally proceed with the default close behavior
        super().closeEvent(event)
        
    def _on_secondary_screen_changed(self, *_):
        """Handle live updates to the selected secondary screen"""
        if not self.secondary_display:
            return

        #print(f"[EVENT] _on_secondary_screen_changed triggered")

        settings = self.settings_controller.get_settings()
        #print(f"Settings screen index: {settings.display.secondary_screen_index}")
        #print(f"Settings screen name: {settings.display.secondary_screen_name}")

        screen = ScreenHandler.get_configured_screen(settings, is_primary=False)
        if screen:
            #print(f"Resolved screen: {screen.name()} — {screen.geometry().width()}x{screen.geometry().height()}")
            QTimer.singleShot(500, lambda: self._move_secondary_display(screen))
        else:
            print("[WARNING] Could not resolve a valid screen for secondary display.")

    def _move_secondary_display(self, screen):
        """Safely move the secondary display to the selected screen after a delay"""
        if not self.secondary_display or not screen:
            return

        # Insert user alert and log if secondary screen is the same as primary
        primary_screen = QApplication.primaryScreen()
        if screen == primary_screen:
            QTimer.singleShot(0, lambda: QMessageBox.information(
                self,
                "Same Screen Selected",
                "The primary and secondary screens are the same. This may cause overlapping windows."
            ))

        geometry = screen.geometry()
        self.secondary_display.setGeometry(geometry)
        self.secondary_display.show()
        QTimer.singleShot(200, lambda: self.secondary_display.showFullScreen())
        #print(f"[FIXED] Moved secondary display to screen: {screen.name()}")
    # The following methods were used for lazy-loading and are now removed: