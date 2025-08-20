#!/usr/bin/env python
"""
Update Box Configuration

This script updates the Box configuration to use the new private key.
"""
import os
import json
import sys

def update_config():
    """Update the Box configuration to use the new private key."""
    config_file = '218068865_0vdlqxdg_config.json'
    
    try:
        # Check if the new private key exists
        if not os.path.exists('new_private_key.pem'):
            print("Error: new_private_key.pem not found!")
            return False
            
        # Check if the config file exists
        if os.path.exists(config_file):
            # Load the config file
            with open(config_file, 'r') as f:
                config = json.load(f)
                
            # Update the private_key_path
            config['boxAppSettings']['appAuth']['privateKey'] = 'new_private_key.pem'
            
            # Save the updated config
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)
                
            print(f"Updated {config_file} to use new_private_key.pem")
            
            # Set environment variables
            os.environ['BOX_PRIVATE_KEY_PATH'] = os.path.abspath('new_private_key.pem')
            print(f"Set BOX_PRIVATE_KEY_PATH={os.environ['BOX_PRIVATE_KEY_PATH']}")
            
            return True
        else:
            print(f"Error: {config_file} not found!")
            return False
    except Exception as e:
        print(f"Error updating config: {e}")
        return False

if __name__ == '__main__':
    if update_config():
        print("Configuration updated successfully. Please restart the server.")
    else:
        print("Failed to update configuration.")
        sys.exit(1) 