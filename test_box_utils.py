#!/usr/bin/env python
"""
A simple script to test Box integration after fixing the utils module.
"""
import os
import sys
import django

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portal_project.settings')
django.setup()

from core.utils import get_box_client
import logging

logging.basicConfig(level=logging.INFO)

def main():
    """Test that the utils module can successfully initialize a Box client."""
    try:
        print("Attempting to initialize Box client using core.utils...")
        client = get_box_client()
        print(f"Success! Box client initialized. User: {client.user().get().name}")
        
        # Test access to a folder
        try:
            root_folder = client.folder(folder_id='0').get()
            print(f"Successfully accessed root folder: {root_folder.name}")
        except Exception as folder_error:
            print(f"Error accessing root folder: {folder_error}")
            
        return True
    except Exception as e:
        print(f"Error initializing Box client: {e}")
        return False

if __name__ == "__main__":
    success = main()
    print("\nTest result:", "PASSED" if success else "FAILED")
    sys.exit(0 if success else 1) 