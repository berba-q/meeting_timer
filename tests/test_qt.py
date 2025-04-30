#!/usr/bin/env python3
"""
A minimal PyQt test script to diagnose platform plugin issues.
This script does everything possible to help PyQt find its plugins.
"""
import os
import sys
from pathlib import Path
import PyQt6.QtCore

# Print Python and environment info
print(f"Python version: {sys.version}")
print(f"Platform: {sys.platform}")
print(f"Executable: {sys.executable}")

# Try different plugin paths - ensure this is done BEFORE importing PyQt
possible_plugin_dirs = [
    # Standard locations
    Path(sys.executable).parent.parent / "lib/python3.11/site-packages/PyQt6/Qt6/plugins",
    Path.home() / ".venv/lib/python3.11/site-packages/PyQt6/Qt6/plugins",
    Path.cwd() / ".venv/lib/python3.11/site-packages/PyQt6/Qt6/plugins",
    # Hard-coded path from your environment
    Path("/Users/griffithsobli-laryea/Documents/meeting_timer/.venv/lib/python3.11/site-packages/PyQt6/Qt6/plugins")
]

# Try to find a valid plugins directory and platforms subdirectory
for plugin_dir in possible_plugin_dirs:
    platforms_dir = plugin_dir / "platforms"
    if platforms_dir.exists():
        print(f"Found platforms dir: {platforms_dir}")
        os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(platforms_dir)
        os.environ["QT_PLUGIN_PATH"] = str(plugin_dir)
        break

# Set additional Qt environment variables for macOS
os.environ["QT_MAC_WANTS_LAYER"] = "1"
# Try offscreen as fallback
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Print relevant environment variables
print(f"QT_QPA_PLATFORM_PLUGIN_PATH: {os.environ.get('QT_QPA_PLATFORM_PLUGIN_PATH', 'Not set')}")
print(f"QT_PLUGIN_PATH: {os.environ.get('QT_PLUGIN_PATH', 'Not set')}")
print(f"QT_MAC_WANTS_LAYER: {os.environ.get('QT_MAC_WANTS_LAYER', 'Not set')}")
print(f"QT_QPA_PLATFORM: {os.environ.get('QT_QPA_PLATFORM', 'Not set')}")

try:
    print("\nTrying to import PyQt6...")
    import PyQt6
    print(f"PyQt6 version: {PyQt6.QtCore.PYQT_VERSION_STR}")
    print(f"Qt version: {PyQt6.QtCore.QT_VERSION_STR}")
    print(f"PyQt6 path: {PyQt6.__file__}")
    
    # Check if Qt plugins directory is in the expected location
    qt_plugins_dir = Path(PyQt6.__file__).parent / "Qt6" / "plugins"
    print(f"Qt plugins directory exists: {qt_plugins_dir.exists()}")
    
    if qt_plugins_dir.exists():
        platforms_dir = qt_plugins_dir / "platforms"
        print(f"Platforms directory exists: {platforms_dir.exists()}")
        
        if platforms_dir.exists():
            print(f"Platforms directory contents: {list(platforms_dir.glob('*'))}")
            
            # Force set plugin paths based on the actual location
            os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(platforms_dir)
            os.environ["QT_PLUGIN_PATH"] = str(qt_plugins_dir)
            print(f"Updated QT_QPA_PLATFORM_PLUGIN_PATH: {os.environ.get('QT_QPA_PLATFORM_PLUGIN_PATH')}")
except ImportError as e:
    print(f"Failed to import PyQt6: {e}")
    sys.exit(1)

print("\nTrying to create QApplication...")
try:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import QTimer
    
    app = QApplication([])
    print("QApplication created successfully!")
    
    def quit_app():
        print("Application quitting normally.")
        app.quit()
    
    # Set a timer to quit after 1 second
    QTimer.singleShot(1000, quit_app)
    
    print("Starting QApplication event loop...")
    sys.exit(app.exec())
except Exception as e:
    print(f"Error creating QApplication: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)