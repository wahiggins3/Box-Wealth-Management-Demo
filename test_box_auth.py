#!/usr/bin/env python
"""
Box Authentication Test Script

This script tests the Box authentication configuration and provides detailed output
to help debug authentication issues.
"""

import os
import sys
import logging
import traceback
from pathlib import Path
from django.core.wsgi import get_wsgi_application

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portal_project.settings')
application = get_wsgi_application()

# Now imports from the project will work
from boxsdk import Client, JWTAuth
from boxsdk.exception import BoxAPIException
from django.conf import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_auth():
    """Tests the Box authentication and returns the authenticated client."""
    try:
        # Log the Box configuration values that we're using
        logger.info("Box Configuration:")
        logger.info(f"CLIENT_ID: {'Set' if settings.BOX_CLIENT_ID else 'Not set'} - {settings.BOX_CLIENT_ID}")
        logger.info(f"CLIENT_SECRET: {'Set' if settings.BOX_CLIENT_SECRET else 'Not set'}")
        logger.info(f"ENTERPRISE_ID: {'Set' if settings.BOX_ENTERPRISE_ID else 'Not set'} - {settings.BOX_ENTERPRISE_ID}")
        logger.info(f"JWT_KEY_ID: {'Set' if settings.BOX_JWT_KEY_ID else 'Not set'} - {settings.BOX_JWT_KEY_ID}")
        logger.info(f"PRIVATE_KEY_PATH: {'Set and exists' if settings.BOX_PRIVATE_KEY_PATH and Path(settings.BOX_PRIVATE_KEY_PATH).exists() else 'Not set or does not exist'} - {settings.BOX_PRIVATE_KEY_PATH}")
        logger.info(f"PRIVATE_KEY_PASSPHRASE: {'Set' if settings.BOX_JWT_PRIVATE_KEY_PASSPHRASE else 'Not set'}")
        
        # Initialize the JWT auth object
        auth = JWTAuth(
            client_id=settings.BOX_CLIENT_ID,
            client_secret=settings.BOX_CLIENT_SECRET,
            enterprise_id=settings.BOX_ENTERPRISE_ID,
            jwt_key_id=settings.BOX_JWT_KEY_ID,
            rsa_private_key_file_sys_path=settings.BOX_PRIVATE_KEY_PATH,
            rsa_private_key_passphrase=settings.BOX_JWT_PRIVATE_KEY_PASSPHRASE.encode() if settings.BOX_JWT_PRIVATE_KEY_PASSPHRASE else None,
        )
        
        logger.info("JWT Auth object created successfully")
        
        # Authenticate and get the access token
        try:
            access_token = auth.authenticate_instance()
            logger.info(f"Access token obtained successfully (length: {len(access_token) if access_token else 'None'})")
        except Exception as e:
            logger.error(f"Error during authentication: {e}")
            raise
        
        # Create the client
        client = Client(auth)
        logger.info("Box client created successfully")
        
        # Test the client by getting the current user
        try:
            current_user = client.user().get()
            logger.info(f"Successfully retrieved current user: {current_user.name} (ID: {current_user.id})")
        except Exception as e:
            logger.error(f"Error retrieving current user: {e}")
            raise
        
        # Test getting root folder items
        try:
            items = list(client.folder(folder_id='0').get_items(limit=10))
            logger.info(f"Successfully retrieved {len(items)} items from root folder")
            for item in items[:5]:  # Show first 5 items
                logger.info(f"- {item.name} ({item.type}, ID: {item.id})")
        except Exception as e:
            logger.error(f"Error retrieving root folder items: {e}")
            raise
            
        # Test downscoping a token
        try:
            # Get the first folder we can find
            folders = [item for item in items if item.type == 'folder']
            if folders:
                test_folder = folders[0]
                logger.info(f"Testing downscope token with folder: {test_folder.name} (ID: {test_folder.id})")
                
                # Define scopes
                scopes = ['base_explorer', 'item_preview', 'item_upload']
                
                # Generate the downscoped token
                box_response = client.downscope_token(
                    scopes=scopes,
                    item=client.folder(folder_id=test_folder.id)
                )
                
                downscoped_token = box_response['access_token']
                logger.info(f"Successfully generated downscoped token (length: {len(downscoped_token) if downscoped_token else 'None'})")
            else:
                logger.warning("No folders found to test downscoping")
        except Exception as e:
            logger.error(f"Error testing downscoped token: {e}")
            logger.error(traceback.format_exc())
        
        return client
        
    except Exception as e:
        logger.error(f"Box authentication failed: {e}")
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    try:
        logger.info("Starting Box authentication test")
        client = test_auth()
        logger.info("Box authentication test completed successfully")
    except Exception as e:
        logger.error(f"Box authentication test failed: {e}")
        sys.exit(1) 