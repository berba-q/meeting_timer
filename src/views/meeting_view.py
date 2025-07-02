"""
Meeting view component for displaying and managing meeting parts.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QTreeWidget, QTreeWidgetItem, QHeaderView,
    QSizePolicy, QSpacerItem, QMenu, QDialog, QFormLayout, QLineEdit,
    QSpinBox, QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSlot, QSize
from PyQt6.QtGui import QAction, QColor, QBrush, QIcon, QFont

from src.controllers.meeting_controller import MeetingController
from src.controllers.timer_controller import TimerController
from src.models.meeting import Meeting, MeetingSection, MeetingPart


class PartEditDialog(QDialog):
    """Dialog for editing a meeting part"""
    
    def __init__(self, part: MeetingPart, parent=None):
        super().__init__(parent)
        self.part = part
        self.setWindowTitle(self.tr("Edit Part"))
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the dialog UI"""
        layout = QFormLayout(self)
        
        # Title field
        self.title_edit = QLineEdit(self.part.title)
        layout.addRow(self.tr("Title:"), self.title_edit)
        
        # Duration field
        self.duration_spin = QSpinBox()
        self.duration_spin.setMinimum(1)
        self.duration_spin.setMaximum(120)
        self.duration_spin.setValue(self.part.duration_minutes)
        layout.addRow(self.tr("Duration (minutes):"), self.duration_spin)

        # Presenter field
        self.presenter_edit = QLineEdit(self.part.presenter)
        layout.addRow(self.tr("Presenter:"), self.presenter_edit)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def get_updated_part(self) -> MeetingPart:
        """Get the updated part data"""
        return MeetingPart(
            title=self.title_edit.text(),
            duration_minutes=self.duration_spin.value(),
            presenter=self.presenter_edit.text(),
            notes=self.part.notes,
            is_completed=self.part.is_completed
        )


class MeetingView(QWidget):
    """Widget for displaying and managing meeting parts"""
    
    def __init__(self, meeting_controller: MeetingController, 
                 timer_controller: TimerController, parent=None):
        super().__init__(parent)
        self.meeting_controller = meeting_controller
        self.timer_controller = timer_controller
        
        # Current meeting
        self.meeting = None
        
        # Setup UI
        self._setup_ui()
        
        # Connect signals
        self._connect_signals()
    
    def _setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        
        # Meeting header
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel(self.tr("No Meeting Selected"))
        self.title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Add header layout
        layout.addLayout(header_layout)
        
        # Parts tree
        self.parts_tree = QTreeWidget()
        self.parts_tree.setHeaderLabels([self.tr("Title"), self.tr("Duration"), self.tr("Status")])
        self.parts_tree.setColumnWidth(0, 400)  # Set width for title column
        self.parts_tree.setColumnWidth(1, 100)  # Set width for duration column
        self.parts_tree.setAlternatingRowColors(True)
        self.parts_tree.setIndentation(20)
        
        # Connect double-click to jump to part
        self.parts_tree.itemDoubleClicked.connect(self._part_double_clicked)
        
        # Enable context menu
        self.parts_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.parts_tree.customContextMenuRequested.connect(self._show_context_menu)
        
        # Set header properties
        header = self.parts_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        
        # Add to layout
        layout.addWidget(self.parts_tree)
    
    def _connect_signals(self):
        """Connect controller signals"""
        self.timer_controller.part_changed.connect(self._part_changed)
        self.timer_controller.part_completed.connect(self._part_completed)
    
    def set_meeting(self, meeting: Meeting):
        """Set the current meeting to display"""
        self.meeting = meeting
        # Clear the tree first
        self.parts_tree.clear()
        self._update_display()
    
    def _update_display(self):
        """Update the display with current meeting data"""
        if not self.meeting:
            self.title_label.setText(self.tr("No Meeting Selected"))
            self.parts_tree.clear()
            return
        
        # Update title
        date_str = self.meeting.date.strftime("%Y-%m-%d")
        self.title_label.setText(self.tr(f"{self.meeting.title} ({date_str})"))
        
        # Clear existing items
        self.parts_tree.clear()
        
        # Add sections and parts
        for section_index, section in enumerate(self.meeting.sections):
            # Create section item
            section_item = QTreeWidgetItem(self.parts_tree)
            section_item.setText(0, section.title)
            section_item.setText(1, f"{section.total_duration_minutes} min")
            section_item.setData(0, Qt.ItemDataRole.UserRole, ("section", section_index))
            
            # Set bold font for section
            font = section_item.font(0)
            font.setBold(True)
            section_item.setFont(0, font)
            
            # Set background color
            section_item.setBackground(0, QBrush(QColor(240, 240, 240)))
            section_item.setBackground(1, QBrush(QColor(240, 240, 240)))
            section_item.setBackground(2, QBrush(QColor(240, 240, 240)))
            
            # Add parts as children
            for part_index, part in enumerate(section.parts):
                part_item = QTreeWidgetItem(section_item)
                # check if songs are part of the meeting
                is_song_part = "song" in part.title.lower()
                part_item.setText(0, part.title)
                part_item.setText(1, f"{part.duration_minutes} min")
                
                # If it's a song part, make it visually distinct
                if is_song_part:
                    part_item.setForeground(0, QBrush(QColor(74, 144, 226)))  # Blue color for songs
                
                # Store additional data for context menu
                global_part_index = self._get_global_part_index(section_index, part_index)
                part_item.setData(0, Qt.ItemDataRole.UserRole, ("part", global_part_index))
                part_item.setData(0, Qt.ItemDataRole.UserRole + 1, section_index)
                part_item.setData(0, Qt.ItemDataRole.UserRole + 2, part_index)
                
                # Set status
                if part.is_completed:
                    part_item.setText(2, self.tr("Completed"))
                    part_item.setForeground(2, QBrush(QColor(0, 128, 0)))  # Green
                else:
                    part_item.setText(2, self.tr("Pending"))

        # Expand all sections
        self.parts_tree.expandAll()
    
    def highlight_part(self, global_part_index: int):
        """Highlight the current part in the tree"""
        # Iterate through all top-level items (sections)
        for section_index in range(self.parts_tree.topLevelItemCount()):
            section_item = self.parts_tree.topLevelItem(section_index)
            
            # Iterate through child items (parts)
            for part_index in range(section_item.childCount()):
                part_item = section_item.child(part_index)
                
                # Get stored global part index
                item_type, item_index = part_item.data(0, Qt.ItemDataRole.UserRole)
                
                if item_type == "part" and item_index == global_part_index:
                    # Set background color for current part
                    part_item.setBackground(0, QBrush(QColor(255, 240, 200)))  # Light yellow
                    part_item.setBackground(1, QBrush(QColor(255, 240, 200)))
                    part_item.setBackground(2, QBrush(QColor(255, 240, 200)))
                    
                    # Set as current item and make visible
                    self.parts_tree.setCurrentItem(part_item)
                    self.parts_tree.scrollToItem(part_item)
                    
                    # Update status text
                    part_item.setText(2, self.tr("Current"))
                    part_item.setForeground(2, QBrush(QColor(0, 0, 255)))  # Blue
                else:
                    # Reset background if not the current part
                    if item_type == "part":
                        part_item.setBackground(0, QBrush())
                        part_item.setBackground(1, QBrush())
                        part_item.setBackground(2, QBrush())
    
    def _part_changed(self, part, global_part_index):
        """Handle part change from timer controller"""
        self.highlight_part(global_part_index)
    
    def _part_completed(self, global_part_index):
        """Handle part completion"""
        # Find the part item in the tree
        for section_index in range(self.parts_tree.topLevelItemCount()):
            section_item = self.parts_tree.topLevelItem(section_index)
            
            for part_index in range(section_item.childCount()):
                part_item = section_item.child(part_index)
                
                item_type, item_index = part_item.data(0, Qt.ItemDataRole.UserRole)
                
                if item_type == "part" and item_index == global_part_index:
                    # Update status
                    part_item.setText(2, self.tr("Completed"))
                    part_item.setForeground(2, QBrush(QColor(0, 128, 0)))  # Green
                    break
    
    def _part_double_clicked(self, item, column):
        """Handle double-click on a part"""
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        
        if not item_data:
            return
        
        item_type, item_index = item_data
        
        if item_type == "part":
            # Jump to this part
            self.timer_controller.jump_to_part(item_index)
    
    def _show_context_menu(self, position):
        """Show context menu for parts"""
        item = self.parts_tree.itemAt(position)
        
        if item:
            item_data = item.data(0, Qt.ItemDataRole.UserRole)
            
            if item_data:
                item_type, item_index = item_data
                
                menu = QMenu()
                
                if item_type == "part":
                    # Part context menu
                    start_action = QAction(self.tr("Start This Part"), self)
                    start_action.triggered.connect(lambda: self.timer_controller.jump_to_part(item_index))
                    menu.addAction(start_action)
                    
                    # Add edit action
                    edit_action = QAction(self.tr("Edit Part"), self)
                    edit_action.triggered.connect(lambda: self._edit_part(item))
                    menu.addAction(edit_action)
                    
                    # Add remove action
                    remove_action = QAction(self.tr("Remove Part"), self)
                    remove_action.triggered.connect(lambda: self._remove_part(item))
                    menu.addAction(remove_action)
                    
                    # Add move actions if appropriate
                    section_index = item.data(0, Qt.ItemDataRole.UserRole + 1)
                    part_index = item.data(0, Qt.ItemDataRole.UserRole + 2)
                    section = self.meeting.sections[section_index]
                    
                    # Move up action (if not the first part)
                    if part_index > 0:
                        move_up_action = QAction(self.tr("Move Up"), self)
                        move_up_action.triggered.connect(lambda: self._move_part_up(item))
                        menu.addAction(move_up_action)
                    
                    # Move down action (if not the last part)
                    if part_index < len(section.parts) - 1:
                        move_down_action = QAction(self.tr("Move Down"), self)
                        move_down_action.triggered.connect(lambda: self._move_part_down(item))
                        menu.addAction(move_down_action)
                
                elif item_type == "section":
                    # Section context menu
                    # Add section-specific actions here
                    pass
                
                if menu.actions():
                    menu.exec(self.parts_tree.mapToGlobal(position))
    
    def _edit_part(self, item):
        """Edit the selected part"""
        if not self.meeting:
            return
        
        # Get section and part indices
        section_index = item.data(0, Qt.ItemDataRole.UserRole + 1)
        part_index = item.data(0, Qt.ItemDataRole.UserRole + 2)
        
        # Get the part to edit
        section = self.meeting.sections[section_index]
        part = section.parts[part_index]
        
        # Create and show edit dialog
        dialog = PartEditDialog(part, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Update part with new values
            updated_part = dialog.get_updated_part()
            
            # Update the part in the model
            section.parts[part_index] = updated_part
            
            # Update the display
            item.setText(0, updated_part.title)
            item.setText(1, f"{updated_part.duration_minutes} min")
            
            # Update the part using the controller
            self.meeting_controller.update_part(self.meeting, section_index, part_index, updated_part)
    
    def _remove_part(self, item):
        """Remove the selected part"""
        if not self.meeting:
            return
        
        # Get section and part indices
        section_index = item.data(0, Qt.ItemDataRole.UserRole + 1)
        part_index = item.data(0, Qt.ItemDataRole.UserRole + 2)
        
        # Confirm removal
        from PyQt6.QtWidgets import QMessageBox
        confirm = QMessageBox.question(
            self, 
            self.tr("Confirm Remove Part"), 
            self.tr("Are you sure you want to remove this part?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if confirm == QMessageBox.StandardButton.Yes:
            # Remove the part using the controller
            self.meeting_controller.remove_part(self.meeting, section_index, part_index)
            
            # Update the display
            self._update_display()
    
    def _move_part_up(self, item):
        """Move the selected part up in its section"""
        if not self.meeting:
            return
        
        # Get section and part indices
        section_index = item.data(0, Qt.ItemDataRole.UserRole + 1)
        part_index = item.data(0, Qt.ItemDataRole.UserRole + 2)
        
        # Check if we can move up
        if part_index <= 0:
            return
        
        # Get the parts
        section = self.meeting.sections[section_index]
        parts = section.parts
        
        # Swap the parts
        parts[part_index], parts[part_index-1] = parts[part_index-1], parts[part_index]
        
        # Save the updated meeting
        self.meeting_controller.save_meeting(self.meeting)
        
        # Update the display
        self._update_display()
        
        # Re-select the moved part
        self._select_part(section_index, part_index-1)
    
    def _move_part_down(self, item):
        """Move the selected part down in its section"""
        if not self.meeting:
            return
        
        # Get section and part indices
        section_index = item.data(0, Qt.ItemDataRole.UserRole + 1)
        part_index = item.data(0, Qt.ItemDataRole.UserRole + 2)
        
        # Check if we can move down
        section = self.meeting.sections[section_index]
        if part_index >= len(section.parts) - 1:
            return
        
        # Swap the parts
        parts = section.parts
        parts[part_index], parts[part_index+1] = parts[part_index+1], parts[part_index]
        
        # Save the updated meeting
        self.meeting_controller.save_meeting(self.meeting)
        
        # Update the display
        self._update_display()
        
        # Re-select the moved part
        self._select_part(section_index, part_index+1)
    
    def _select_part(self, section_index, part_index):
        """Select a part in the tree"""
        # Get the section item
        if section_index < self.parts_tree.topLevelItemCount():
            section_item = self.parts_tree.topLevelItem(section_index)
            
            # Get the part item
            if part_index < section_item.childCount():
                part_item = section_item.child(part_index)
                
                # Select the part
                self.parts_tree.setCurrentItem(part_item)
                self.parts_tree.scrollToItem(part_item)
    
    def _get_global_part_index(self, section_index, part_index):
        """Convert section and part indices to global part index"""
        global_index = 0
        
        for i in range(section_index):
            global_index += len(self.meeting.sections[i].parts)
        
        global_index += part_index
        return global_index