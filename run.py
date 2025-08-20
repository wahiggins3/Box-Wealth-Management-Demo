#!/usr/bin/env python
"""
Simple script to start the Django server with cleaner output
"""
import os
import sys
import subprocess

def main():
    """Run the Django development server"""
    try:
        print("Starting Django development server on port 8001...")
        # Execute the django server command with a different port
        result = subprocess.run(
            [sys.executable, "manage.py", "runserver", "8001"],
            check=True,
            text=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error running server: {e}")
        return False
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        return True

if __name__ == "__main__":
    sys.exit(0 if main() else 1) 