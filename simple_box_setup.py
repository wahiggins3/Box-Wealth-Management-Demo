#!/usr/bin/env python
"""
Simple Box Configuration Setup

This script creates a .env file with Box configuration without requiring interactive input.
"""

import os
from pathlib import Path

# Configuration values - REPLACE THESE WITH YOUR ACTUAL VALUES
BOX_CONFIG = {
    # Django settings
    'SECRET_KEY': 'django-insecure-qj&n7m@h0=x&^x^13!t9&7@c8_@=w1a@*g@1h+w%g9n*k7d%@d',
    'DEBUG': 'True',
    'ALLOWED_HOSTS': 'localhost,127.0.0.1',
    
    # Box API settings - you need to replace these with your actual values
    'BOX_CLIENT_ID': '',           # Replace with your actual Box Client ID
    'BOX_CLIENT_SECRET': '',       # Replace with your actual Box Client Secret
    'BOX_ENTERPRISE_ID': '',       # Replace with your actual Box Enterprise ID
    'BOX_JWT_KEY_ID': '',          # Replace with your actual Box JWT Key ID
    
    # You can either use a private key file path OR include the key content directly
    'BOX_PRIVATE_KEY_PATH': '/Users/bsjulson/BoxProjects/financial-portal/private_key.pem',    # Replace with the path to your private key file
    
    # OR set the private key content directly (multi-line string with proper line breaks)
    # Example: '-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC7VJTUt9Us8cKj\n...\n-----END PRIVATE KEY-----'
    'BOX_PRIVATE_KEY_CONTENT': '',  # Replace with your actual private key content
    
    'BOX_JWT_PRIVATE_KEY_PASSPHRASE': 'boxbox',  # Replace with your key passphrase (or leave empty)
}

def create_env_file():
    """Create a .env file with the specified configuration"""
    script_dir = Path(__file__).resolve().parent
    env_file = script_dir / '.env'
    
    # Create the .env file content
    env_content = """# Django settings
SECRET_KEY={SECRET_KEY}
DEBUG={DEBUG}
ALLOWED_HOSTS={ALLOWED_HOSTS}

# Box API Configuration
BOX_CLIENT_ID={BOX_CLIENT_ID}
BOX_CLIENT_SECRET={BOX_CLIENT_SECRET}
BOX_ENTERPRISE_ID={BOX_ENTERPRISE_ID}
BOX_JWT_KEY_ID={BOX_JWT_KEY_ID}
""".format(**BOX_CONFIG)

    # Add either path or content, not both
    if BOX_CONFIG['BOX_PRIVATE_KEY_PATH']:
        env_content += "BOX_PRIVATE_KEY_PATH={BOX_PRIVATE_KEY_PATH}\n".format(**BOX_CONFIG)
    elif BOX_CONFIG['BOX_PRIVATE_KEY_CONTENT']:
        env_content += "BOX_PRIVATE_KEY_CONTENT={BOX_PRIVATE_KEY_CONTENT}\n".format(**BOX_CONFIG)
    
    # Add passphrase if provided
    if BOX_CONFIG['BOX_JWT_PRIVATE_KEY_PASSPHRASE']:
        env_content += "BOX_JWT_PRIVATE_KEY_PASSPHRASE={BOX_JWT_PRIVATE_KEY_PASSPHRASE}\n".format(**BOX_CONFIG)
    
    # Write to the .env file
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f".env file created successfully at: {env_file}")
    print("\nNext steps:")
    print("1. Restart your Django development server")
    print("2. Navigate to the Documents tab to test your Box integration")

if __name__ == "__main__":
    # Check if configuration is provided
    missing = [key for key in ['BOX_CLIENT_ID', 'BOX_CLIENT_SECRET', 'BOX_ENTERPRISE_ID', 'BOX_JWT_KEY_ID'] 
               if not BOX_CONFIG[key]]
    
    # Either private key path or content must be provided
    if not BOX_CONFIG['BOX_PRIVATE_KEY_PATH'] and not BOX_CONFIG['BOX_PRIVATE_KEY_CONTENT']:
        missing.append('BOX_PRIVATE_KEY_PATH or BOX_PRIVATE_KEY_CONTENT')
    
    if missing:
        print("ERROR: You need to edit this script and provide values for:")
        for key in missing:
            print(f"  - {key}")
        print("\nPlease open simple_box_setup.py in a text editor and fill in the missing values.")
        exit(1)
    
    create_env_file() 