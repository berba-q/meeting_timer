"""
Dialog for editing weekend meeting songs in the OnTime Meeting Timer application.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFormLayout, QSpinBox, QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import Qt

class WeekendSongEditorDialog(QDialog):
    """Dialog for editing weekend meeting songs"""
    
    def __init__(self, meeting, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Edit Weekend Meeting Songs"))
        self.meeting = meeting
        self.song_fields = []

        # Ensure dialog appears on top of the main window (especially on Windows)
        self.setWindowFlags(
            self.windowFlags()
            & ~Qt.WindowType.WindowContextHelpButtonHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.raise_()
        self.activateWindow()

        # Setup UI
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        
        # Add description
        description = QLabel(
            self.tr("Enter song numbers for the weekend meeting. Leave empty for songs "
            "that don't require a number (like theme songs or musical items).")
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Create form for songs
        form_layout = QFormLayout()
        
        # Find all parts that contain "song" in their title
        song_parts = []
        for section in self.meeting.sections:
            for part in section.parts:
                if "song" in part.title.lower():
                    song_parts.append((section.title, part))
        
        # Add fields for each song
        for section_title, part in song_parts:
            # Extract existing song number if present
            existing_number = None
            import re
            song_match = re.search(r'song\s+(\d+)', part.title.lower())
            if song_match:
                existing_number = int(song_match.group(1))
            
            # Create spin box for song number
            spin_box = QSpinBox()
            spin_box.setRange(1, 150)  # Reasonable range for song numbers
            spin_box.setSpecialValueText("")  # Empty for no number
            if existing_number:
                spin_box.setValue(existing_number)
            
            # Create label with context
            if "prayer" in part.title.lower():
                if "opening" in part.title.lower() or "public" in section_title.lower():
                    label_text = f"{self.tr('Opening Song')} ({section_title}):"
                elif "concluding" in part.title.lower() or "watchtower" in section_title.lower():
                    label_text = f"{self.tr('Concluding Song')} ({section_title}):"
                else:
                    label_text = f"{self.tr('Song and Prayer')} ({section_title}):"
            else:
                label_text = f"{self.tr('Song')} ({section_title}):"
            
            # Add to form
            form_layout.addRow(label_text, spin_box)
            
            # Store reference to the spin box along with the part
            self.song_fields.append((spin_box, part))
        
        layout.addLayout(form_layout)
        
        # Add dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def accept(self):
        """Handle dialog acceptance"""
        # Update song titles with numbers
        for spin_box, part in self.song_fields:
            song_number = spin_box.value()
            
            if song_number > 0:  # If a song number was provided
                part_title_lower = part.title.lower()
                
                # Format based on whether it includes prayer
                if "prayer" in part_title_lower:
                    if "opening" in part_title_lower:
                        part.title = f"{self.tr('Song')} {song_number} {self.tr('and Opening Prayer')}"
                    elif "concluding" in part_title_lower:
                        part.title = f"{self.tr('Song')} {song_number} {self.tr('and Concluding Prayer')}"
                    else:
                        part.title = f"{self.tr('Song')} {song_number} {self.tr('and Prayer')}"
                else:
                    part.title = f"{self.tr('Song')} {song_number}"
        
        super().accept()