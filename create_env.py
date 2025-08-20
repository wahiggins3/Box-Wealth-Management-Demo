#!/usr/bin/env python
"""
Create .env File for Box Configuration

This script guides you through setting up the Box API credentials
needed for the financial portal.
"""

import os
from pathlib import Path
import getpass

def main():
    print("\n=== Box Configuration Setup ===\n")
    print("This script will help you create a .env file with your Box API credentials.")
    print("You'll need the following information from your Box Developer Console:")
    print("  - Client ID")
    print("  - Client Secret")
    print("  - Enterprise ID")
    print("  - JWT Key ID")
    print("  - Path to your private key file (.pem)")
    print("  - Private key passphrase (if your key is encrypted)")
    print("\nNote: You can find these details in your Box Developer Console: https://app.box.com/developers/console")
    
    proceed = input("\nDo you want to proceed? (y/n): ").lower()
    if proceed != 'y':
        print("Setup cancelled.")
        return

    # Get the directory where the script is located
    script_dir = Path(__file__).resolve().parent
    env_file = script_dir / '.env'
    
    # Check if .env already exists
    if env_file.exists():
        overwrite = input(f"\nA .env file already exists at {env_file}. Overwrite? (y/n): ").lower()
        if overwrite != 'y':
            print("Setup cancelled.")
            return
    
    # Get Django settings
    print("\n=== Django Settings ===")
    secret_key = input("Django SECRET_KEY (leave blank for default): ") or 'django-insecure-qj&n7m@h0=x&^x^13!t9&7@c8_@=w1a@*g@1h+w%g9n*k7d%@d'
    debug = input("DEBUG mode (True/False, default is True): ").lower() or 'true'
    allowed_hosts = input("ALLOWED_HOSTS (comma-separated, default is localhost,127.0.0.1): ") or 'localhost,127.0.0.1'
    
    # Get Box settings
    print("\n=== Box API Settings ===")
    box_client_id = input("Box CLIENT_ID: ")
    box_client_secret = input("Box CLIENT_SECRET: ")
    box_enterprise_id = input("Box ENTERPRISE_ID: ")
    box_jwt_key_id = input("Box JWT_KEY_ID: ")
    
    # For the private key path, let's check if the file exists
    while True:
        box_private_key_path = input("Path to your private key file (.pem): ")
        if not box_private_key_path:
            print("Private key path is required.")
            continue
        
        # Expand user directory if present (e.g., ~/my-key.pem)
        expanded_path = os.path.expanduser(box_private_key_path)
        
        if os.path.exists(expanded_path):
            box_private_key_path = expanded_path
            break
        else:
            print(f"File does not exist at: {expanded_path}")
            retry = input("Try again? (y/n): ").lower()
            if retry != 'y':
                print("Setup cancelled.")
                return
    
    # Passphrase is optional
    box_passphrase = getpass.getpass("Box private key passphrase (leave blank if none): ") or ''
    
    # Create the .env file content
    env_content = f"""# Django settings
SECRET_KEY={secret_key}
DEBUG={debug}
ALLOWED_HOSTS={allowed_hosts}

# Box API Configuration
BOX_CLIENT_ID={box_client_id}
BOX_CLIENT_SECRET={box_client_secret}
BOX_ENTERPRISE_ID={box_enterprise_id}
BOX_JWT_KEY_ID={box_jwt_key_id}
BOX_PRIVATE_KEY_PATH={box_private_key_path}
BOX_JWT_PRIVATE_KEY_PASSPHRASE={box_passphrase}
"""
    
    # Write to the .env file
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f"\n✅ .env file created successfully at: {env_file}")
    print("\nNext steps:")
    print("1. Restart your Django development server")
    print("2. Navigate to the Documents tab to test your Box integration")
    print("3. If you encounter issues, check the server logs for details")

if __name__ == "__main__":
    main() 