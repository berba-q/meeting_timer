"""
Create default meeting templates for the OnTime Meeting Timer application.
This script can be run to create default templates in the resources directory,
which will be available to the application.
"""
import os
import sys
from pathlib import Path
import json

# Add parent directory to path to import application modules
script_dir = Path(__file__).parent
parent_dir = script_dir.parent
sys.path.insert(0, str(parent_dir))

# Import from application
from src.models.meeting_template import create_default_templates

if __name__ == "__main__":
    print("Creating default meeting templates...")
    
    # Create default templates
    create_default_templates()
    
    print("Default templates created successfully!")
    
    # List created templates
    template_dir = Path(parent_dir) / "resources" / "templates"
    templates = list(template_dir.glob("*.json"))
    
    print(f"\nCreated {len(templates)} templates:")
    for template_path in templates:
        print(f"- {template_path.name}")