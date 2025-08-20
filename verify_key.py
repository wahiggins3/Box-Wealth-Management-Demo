#!/usr/bin/env python
"""
Verify Private Key

This script verifies that a private key can be properly loaded and is in the correct format.
"""

import sys
import os
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives.asymmetric import rsa
from pathlib import Path
import getpass

def verify_key_file(key_path, passphrase=None):
    """Verify that a key file can be loaded"""
    try:
        # Read the key file
        with open(key_path, 'rb') as f:
            key_data = f.read()
            
        # Try to load the key
        passphrase_bytes = passphrase.encode() if passphrase else None
        key = load_pem_private_key(key_data, password=passphrase_bytes)
        
        # Check if it's an RSA key
        if isinstance(key, rsa.RSAPrivateKey):
            print(f"✅ Successfully loaded RSA private key from {key_path}")
            print(f"   Key size: {key.key_size} bits")
            return True
        else:
            print(f"⚠️ Loaded key is not an RSA key. This may cause issues with Box SDK.")
            return False
    except Exception as e:
        print(f"❌ Error loading key: {str(e)}")
        return False

def verify_key_content(key_content, passphrase=None):
    """Verify that key content can be loaded"""
    try:
        # Process content string to handle escaped newlines
        if '\\n' in key_content:
            key_content = key_content.replace('\\n', '\n')
            
        # Convert to bytes
        key_data = key_content.encode('utf-8')
        
        # Try to load the key
        passphrase_bytes = passphrase.encode() if passphrase else None
        key = load_pem_private_key(key_data, password=passphrase_bytes)
        
        # Check if it's an RSA key
        if isinstance(key, rsa.RSAPrivateKey):
            print(f"✅ Successfully loaded RSA private key from content string")
            print(f"   Key size: {key.key_size} bits")
            return True
        else:
            print(f"⚠️ Loaded key is not an RSA key. This may cause issues with Box SDK.")
            return False
    except Exception as e:
        print(f"❌ Error loading key: {str(e)}")
        
        # Provide more detailed information
        print("\nKey content analysis:")
        lines = key_content.split('\n')
        print(f"- Line count: {len(lines)}")
        if len(lines) >= 2:
            print(f"- First line: {lines[0]}")
            print(f"- Last line: {lines[-1]}")
        
        print("\nCommon issues:")
        print("1. Missing BEGIN/END markers")
        print("2. Extra whitespace or non-PEM content")
        print("3. Incorrect line breaks")
        print("4. Wrong passphrase (if encrypted)")
        return False

def main():
    """Main function"""
    print("\n=== Private Key Verification Tool ===\n")
    
    verification_type = input("Verify (1) key file or (2) key content string? (1/2): ").strip()
    
    if verification_type == "1":
        # Verify key file
        key_path = input("Enter path to private key file: ").strip()
        if not os.path.exists(key_path):
            print(f"Error: File does not exist: {key_path}")
            return
            
        is_encrypted = input("Is the key encrypted? (y/n): ").strip().lower() == 'y'
        passphrase = None
        if is_encrypted:
            passphrase = getpass.getpass("Enter passphrase: ")
            
        verify_key_file(key_path, passphrase)
        
    elif verification_type == "2":
        # Verify key content string
        print("\nPaste your key content (Ctrl+D or Ctrl+Z when finished):")
        key_content = sys.stdin.read().strip()
        
        is_encrypted = input("Is the key encrypted? (y/n): ").strip().lower() == 'y'
        passphrase = None
        if is_encrypted:
            passphrase = getpass.getpass("Enter passphrase: ")
            
        verify_key_content(key_content, passphrase)
        
    else:
        print("Invalid choice. Please enter 1 or 2.")

if __name__ == "__main__":
    main() 