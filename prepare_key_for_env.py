#!/usr/bin/env python
"""
Prepare Private Key for Environment Variable

This script takes a private key file and formats it for inclusion directly
in an environment variable, with proper line breaks.
"""

import sys
import os
from pathlib import Path

def format_key_for_env(key_file_path):
    """Format a private key file for inclusion in an environment variable"""
    try:
        # Read the key file
        with open(key_file_path, 'r') as f:
            key_content = f.read().strip()
        
        # Replace literal newlines with \n for environment variable
        env_formatted_key = key_content.replace('\n', '\\n')
        
        print("\n=== Formatted key for .env file ===")
        print("BOX_PRIVATE_KEY_CONTENT=" + env_formatted_key)
        print("===================================\n")
        
        print("You can copy the above line into your .env file or update simple_box_setup.py")
        
        # Optionally write to a file
        write_to_file = input("Would you like to save this to a file? (y/n): ").lower().strip()
        if write_to_file == 'y':
            output_path = Path('box_key_for_env.txt')
            with open(output_path, 'w') as f:
                f.write("BOX_PRIVATE_KEY_CONTENT=" + env_formatted_key)
            print(f"Saved to {output_path.resolve()}")
        
        return True
    except Exception as e:
        print(f"Error formatting key: {str(e)}")
        return False

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python prepare_key_for_env.py <path_to_private_key.pem>")
        return
    
    key_file_path = sys.argv[1]
    
    if not os.path.exists(key_file_path):
        print(f"Error: The file {key_file_path} does not exist.")
        return
    
    format_key_for_env(key_file_path)

if __name__ == "__main__":
    main() 