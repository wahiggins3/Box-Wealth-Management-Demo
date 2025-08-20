#!/usr/bin/env python
"""
Set up .env file from Box JSON config

This script reads a Box JSON config file and creates a .env file with the proper credentials.
"""
import json
import os
from pathlib import Path

def main():
    """Create .env file from Box JSON config"""
    json_path = Path('218068865_0vdlqxdg_config.json')
    env_path = Path('.env')
    
    # Read the JSON config
    with open(json_path, 'r') as f:
        config = json.load(f)
    
    # Extract the values we need
    box_client_id = config['boxAppSettings']['clientID']
    box_client_secret = config['boxAppSettings']['clientSecret']
    box_enterprise_id = config['enterpriseID']
    box_jwt_key_id = config['boxAppSettings']['appAuth']['publicKeyID']
    box_passphrase = config['boxAppSettings']['appAuth']['passphrase']
    
    # Create the private key file
    private_key = config['boxAppSettings']['appAuth']['privateKey']
    private_key_path = Path('new_private_key.pem')
    with open(private_key_path, 'w') as f:
        f.write(private_key)
    
    print(f"Private key saved to {private_key_path}")
    
    # Create the .env file content
    env_content = f"""# Django settings
SECRET_KEY=django-insecure-qj&n7m@h0=x&^x^13!t9&7@c8_@=w1a@*g@1h+w%g9n*k7d%@d
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Box API Configuration
BOX_CLIENT_ID={box_client_id}
BOX_CLIENT_SECRET={box_client_secret}
BOX_ENTERPRISE_ID={box_enterprise_id}
BOX_JWT_KEY_ID={box_jwt_key_id}
BOX_PRIVATE_KEY_PATH={private_key_path.absolute()}
BOX_JWT_PRIVATE_KEY_PASSPHRASE={box_passphrase}
"""
    
    # Write the .env file
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f".env file created with Box credentials from {json_path}")
    print("Next steps:")
    print("1. Restart your Django development server")
    print("2. Navigate to the Documents tab to test your Box integration")

if __name__ == "__main__":
    main() 