# Simple Box Configuration Verification
import os
import json
from pathlib import Path

# Print Box configuration from .env file
def check_env_file():
    print("\n=== Checking .env file ===")
    env_path = Path('.env')
    if not env_path.exists():
        print("ERROR: .env file not found!")
        return False
    
    with open(env_path, 'r') as f:
        content = f.read()
    
    # Extract and print key variables (hiding sensitive parts)
    env_vars = {}
    for line in content.split('\n'):
        if line.strip() and not line.strip().startswith('#'):
            parts = line.split('=', 1)
            if len(parts) == 2:
                key, value = parts[0].strip(), parts[1].strip()
                env_vars[key] = value
    
    # Print relevant Box config variables
    box_vars = [
        'BOX_CLIENT_ID', 'BOX_CLIENT_SECRET', 'BOX_ENTERPRISE_ID', 
        'BOX_JWT_KEY_ID', 'BOX_PRIVATE_KEY_PATH', 'BOX_PRIVATE_KEY_CONTENT',
        'BOX_JWT_PRIVATE_KEY_PASSPHRASE'
    ]
    
    for var in box_vars:
        if var in env_vars:
            value = env_vars[var]
            # Mask sensitive values
            if var in ['BOX_CLIENT_SECRET', 'BOX_JWT_PRIVATE_KEY_PASSPHRASE']:
                if value:
                    value = value[:4] + '****' + value[-4:] if len(value) > 8 else '****'
            # Show beginning and end of private key content
            elif var == 'BOX_PRIVATE_KEY_CONTENT' and value:
                value = value[:40] + '...' + value[-40:] if len(value) > 80 else value
            
            print(f"{var}: {value}")
        else:
            print(f"{var}: Not set")
    
    # Check if private key path exists
    if 'BOX_PRIVATE_KEY_PATH' in env_vars:
        key_path = env_vars['BOX_PRIVATE_KEY_PATH']
        key_exists = Path(key_path).exists()
        print(f"\nPrivate key file exists: {key_exists}")
        if key_exists:
            print(f"Private key file size: {Path(key_path).stat().st_size} bytes")
            # Print first and last few characters of key file (if not too sensitive)
            with open(key_path, 'r') as f:
                key_content = f.read()
            print(f"Key file begins with: {key_content[:40]}...")
            print(f"Key file ends with: ...{key_content[-40:]}")
    
    return True

# Check Box config JSON file
def check_config_json():
    print("\n=== Checking Box config JSON ===")
    json_files = list(Path('.').glob('*_config.json'))
    if not json_files:
        print("No Box config JSON files found!")
        return False
    
    print(f"Found config files: {', '.join(str(f) for f in json_files)}")
    
    # Read the first config file found
    config_file = json_files[0]
    with open(config_file, 'r') as f:
        try:
            config = json.load(f)
            
            # Extract and print key details (with masking)
            app_settings = config.get('boxAppSettings', {})
            client_id = app_settings.get('clientID', 'Not set')
            client_secret = app_settings.get('clientSecret', 'Not set')
            
            if client_secret and len(client_secret) > 8:
                client_secret = client_secret[:4] + '****' + client_secret[-4:]
            else:
                client_secret = '****'
            
            print(f"Client ID: {client_id}")
            print(f"Client Secret: {client_secret}")
            
            # Check enterprise ID
            enterprise_id = config.get('enterpriseID', 'Not set')
            print(f"Enterprise ID: {enterprise_id}")
            
            # Check app auth settings
            app_auth = app_settings.get('appAuth', {})
            public_key_id = app_auth.get('publicKeyID', 'Not set')
            private_key_file = app_auth.get('privateKey', 'Not set')
            passphrase = app_auth.get('passphrase', 'Not set')
            
            if passphrase and len(passphrase) > 8:
                passphrase = passphrase[:4] + '****' + passphrase[-4:]
            else:
                passphrase = '****' if passphrase else 'Not set'
            
            print(f"Public Key ID: {public_key_id}")
            print(f"Private Key File: {private_key_file}")
            print(f"Passphrase: {passphrase}")
            
            # Check if the private key file referenced in JSON exists
            if private_key_file:
                key_exists = Path(private_key_file).exists()
                print(f"\nPrivate key file from JSON exists: {key_exists}")
                if key_exists:
                    print(f"Private key file size: {Path(private_key_file).stat().st_size} bytes")
            
            return True
        except json.JSONDecodeError:
            print(f"Error: {config_file} is not a valid JSON file!")
            return False

# Compare values between .env and JSON config
def compare_configs():
    print("\n=== Comparing Configurations ===")
    
    # Get .env values
    env_path = Path('.env')
    if not env_path.exists():
        print("ERROR: .env file not found!")
        return False
    
    env_vars = {}
    with open(env_path, 'r') as f:
        for line in f.read().split('\n'):
            if line.strip() and not line.strip().startswith('#'):
                parts = line.split('=', 1)
                if len(parts) == 2:
                    key, value = parts[0].strip(), parts[1].strip()
                    env_vars[key] = value
    
    # Get JSON values
    json_files = list(Path('.').glob('*_config.json'))
    if not json_files:
        print("No Box config JSON files found!")
        return False
    
    with open(json_files[0], 'r') as f:
        try:
            config = json.load(f)
            
            # Extract key values
            app_settings = config.get('boxAppSettings', {})
            json_client_id = app_settings.get('clientID', 'Not set')
            json_enterprise_id = config.get('enterpriseID', 'Not set')
            
            app_auth = app_settings.get('appAuth', {})
            json_key_id = app_auth.get('publicKeyID', 'Not set')
            json_key_file = app_auth.get('privateKey', 'Not set')
            json_passphrase = app_auth.get('passphrase', 'Not set')
            
            # Compare values
            env_client_id = env_vars.get('BOX_CLIENT_ID', 'Not set')
            env_enterprise_id = env_vars.get('BOX_ENTERPRISE_ID', 'Not set')
            env_key_id = env_vars.get('BOX_JWT_KEY_ID', 'Not set')
            env_key_path = env_vars.get('BOX_PRIVATE_KEY_PATH', 'Not set')
            env_passphrase = env_vars.get('BOX_JWT_PRIVATE_KEY_PASSPHRASE', 'Not set')
            
            mismatches = []
            
            if json_client_id != env_client_id:
                mismatches.append(f"Client ID mismatch: JSON={json_client_id}, ENV={env_client_id}")
                
            if json_enterprise_id != env_enterprise_id:
                mismatches.append(f"Enterprise ID mismatch: JSON={json_enterprise_id}, ENV={env_enterprise_id}")
                
            if json_key_id != env_key_id:
                mismatches.append(f"JWT Key ID mismatch: JSON={json_key_id}, ENV={env_key_id}")
                
            # Check if private key file paths align (basename comparison for flexibility)
            if env_key_path and json_key_file:
                env_key_basename = os.path.basename(env_key_path)
                json_key_basename = os.path.basename(json_key_file)
                if env_key_basename != json_key_basename:
                    mismatches.append(f"Private key filename mismatch: JSON={json_key_basename}, ENV={env_key_basename}")
            
            if mismatches:
                print("WARNING: Mismatches found between JSON and .env:")
                for msg in mismatches:
                    print(f"- {msg}")
            else:
                print("All critical values match between JSON and .env")
            
            return len(mismatches) == 0
        except json.JSONDecodeError:
            print(f"Error: {json_files[0]} is not a valid JSON file!")
            return False

if __name__ == "__main__":
    print("Box Configuration Verification Tool")
    print("==================================")
    
    env_ok = check_env_file()
    json_ok = check_config_json()
    configs_match = compare_configs()
    
    print("\n=== Summary ===")
    print(f".env file check: {'OK' if env_ok else 'FAILED'}")
    print(f"Config JSON check: {'OK' if json_ok else 'FAILED'}")
    print(f"Config comparison: {'OK' if configs_match else 'ISSUES FOUND'}")
    
    # Overall assessment
    if env_ok and json_ok and configs_match:
        print("\nBox configuration appears to be consistent.")
        print("If you're still having issues, check that:")
        print("1. The private key file contains a valid key")
        print("2. The Box app in the developer console is properly configured")
        print("3. The environment variables are correctly loaded at runtime")
    else:
        print("\nPotential Box configuration issues found.")
        print("See the details above for specific problems to address.") 