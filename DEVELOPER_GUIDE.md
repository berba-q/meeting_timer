# OnTime - Developer Guide

This guide is intended for developers who want to understand, modify, or contribute to the OnTime Meeting Timer application.

## Project Architecture

The application follows the Model-View-Controller (MVC) pattern:

```
src/
├── models/          # Data models
├── views/           # UI components
├── controllers/     # Logic connecting models and views
├── utils/           # Utility functions and helpers
└── __init__.py
```

### Key Components

1. **Timer Model**: Core timing functionality
2. **Meeting Model**: Meeting data structure
3. **Template System**: Meeting template management
4. **Settings System**: Application configuration
5. **Web Scraper**: Meeting data retrieval

## Development Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/berba-q/meeting_timer.git
cd meeting_timer
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Generate default templates:
```bash
python scripts/create_default_templates.py
```

5. Run the application:
```bash
python main.py
```

## Testing

### Running Tests

```bash
# Run all tests
python -m unittest discover tests

# Run specific test module
python -m unittest tests.test_timer

# Run specific test case
python -m unittest tests.test_timer.TestTimer.test_start_timer
```

### Writing Tests

1. Create test files in the `tests/` directory
2. Use Python's unittest framework
3. Follow naming convention: `test_*.py` for files, `test_*` for methods

Example:

```python
import unittest
from src.models.meeting import Meeting, MeetingType

class TestMeeting(unittest.TestCase):
    def setUp(self):
        # Setup code runs before each test
        self.meeting = Meeting(
            meeting_type=MeetingType.MIDWEEK,
            title="Test Meeting",
            date=datetime.now(),
            start_time=datetime.now().time(),
            sections=[]
        )
    
    def test_total_duration(self):
        # Test code
        self.assertEqual(self.meeting.total_duration_minutes, 0)
        
        # Add a section and test again
        # ...
```

## Code Organization

### Models

Models represent the application's data structures and business logic.

- `timer.py`: Handles timing operations and states
- `meeting.py`: Defines meeting structure
- `meeting_template.py`: Template management system
- `settings.py`: Application settings

### Views

Views are PyQt6 UI components that display data to the user.

- `main_window.py`: Main application window
- `timer_view.py`: Timer display component
- `meeting_view.py`: Meeting parts display
- `settings_view.py`: Settings dialog
- `meeting_editor_dialog.py`: Meeting creation/editing dialog

### Controllers

Controllers manage interactions between models and views.

- `timer_controller.py`: Controls timer operations
- `meeting_controller.py`: Manages meetings
- `settings_controller.py`: Handles settings changes

## Key Interfaces

### Timer Signals

The timer system uses Qt signals to communicate state changes:

```python
# In timer_controller.py
self.timer.time_updated.connect(self._handle_time_update)
self.timer.state_changed.connect(self._handle_state_change)
```

### Meeting Templates

Meeting templates use a simple structure for storing section and part data:

```json
{
  "title": "Midweek Meeting",
  "language": "en",
  "sections": [
    {
      "title": "TREASURES FROM GOD'S WORD",
      "parts": [
        {
          "title": "Opening Song and Prayer",
          "duration_minutes": 5,
          "presenter": ""
        },
        {
          "title": "Bible Reading",
          "duration_minutes": 4,
          "presenter": ""
        }
      ]
    }
  ]
}
```

## Extending the Application

### Adding a New Feature

1. **Plan the feature**:
   - Identify which models need to be updated
   - Design necessary UI components
   - Plan controller updates

2. **Update models** to support the feature

3. **Create or update views** to expose the feature

4. **Connect via controllers** to handle business logic

5. **Add tests** to verify functionality

### Example: Adding Support for Excel Import

1. **Add dependency**:
   ```python
   # requirements.txt
   openpyxl>=3.0.0
   ```

2. **Create utility function**:
   ```python
   # src/utils/excel_importer.py
   import openpyxl
   
   def import_meeting_from_excel(file_path):
       """Import meeting from Excel file"""
       wb = openpyxl.load_workbook(file_path)
       # Convert Excel data to Meeting object
       # ...
       return meeting
   ```

3. **Update meeting controller**:
   ```python
   # src/controllers/meeting_controller.py
   from src.utils.excel_importer import import_meeting_from_excel
   
   def import_meeting_from_excel_file(self, file_path):
       """Import meeting from Excel file"""
       try:
           meeting = import_meeting_from_excel(file_path)
           self.set_current_meeting(meeting)
           return True
       except Exception as e:
           self.error_occurred.emit(str(e))
           return False
   ```

4. **Add UI component**:
   ```python
   # Update main_window.py to add import menu item
   import_action = QAction("Import from Excel", self)
   import_action.triggered.connect(self._import_from_excel)
   file_menu.addAction(import_action)
   
   def _import_from_excel(self):
       file_path, _ = QFileDialog.getOpenFileName(
           self, "Import Meeting", "", "Excel Files (*.xlsx *.xls)"
       )
       if file_path:
           self.meeting_controller.import_meeting_from_excel_file(file_path)
   ```

## Building for Distribution

### PyInstaller Setup

1. Install PyInstaller:
```bash
pip install pyinstaller
```

2. Create a spec file:
```bash
pyi-makespec --windowed --name "JWMeetingTimer" main.py
```

3. Edit the spec file to include required data files:
```python
# JWMeetingTimer.spec
# ...
datas=[
    ('assets', 'assets'),
    ('resources', 'resources'),
],
# ...
```

4. Build the executable:
```bash
pyinstaller JWMeetingTimer.spec
```

## Contributing Guidelines

1. **Fork the repository** and create a feature branch
2. **Make changes** following the project's style guide
3. **Add tests** for new functionality
4. **Run existing tests** to ensure no regressions
5. **Submit a pull request** with a clear description of changes

## Resources

- [PyQt6 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt6/)
- [Qt Documentation](https://doc.qt.io/)
- [Python unittest documentation](https://docs.python.org/3/library/unittest.html)

## License

This project is licensed under the MIT License - see the LICENSE file for details.