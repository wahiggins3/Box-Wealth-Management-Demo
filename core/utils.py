"""
Box API Utilities

This module provides functions for interacting with the Box API.
"""
import os
import logging
from django.conf import settings
from boxsdk import Client, JWTAuth
from boxsdk.exception import BoxAPIException

logger = logging.getLogger(__name__)

def get_box_client():
    """Authenticates with Box and returns the client."""
    try:
        # Log the Box configuration for debugging
        logging.info("Box Configuration:")
        logging.info(f"CLIENT_ID: {'Set' if settings.BOX_CLIENT_ID else 'Not set'}")
        logging.info(f"CLIENT_SECRET: {'Set' if settings.BOX_CLIENT_SECRET else 'Not set'}")
        logging.info(f"ENTERPRISE_ID: {'Set' if settings.BOX_ENTERPRISE_ID else 'Not set'}")
        logging.info(f"JWT_KEY_ID: {'Set' if settings.BOX_JWT_KEY_ID else 'Not set'} (Type: {type(settings.BOX_JWT_KEY_ID)})")
        logging.info(f"PRIVATE_KEY_PATH: {'Set' if settings.BOX_PRIVATE_KEY_PATH else 'Not set'}")
        logging.info(f"PRIVATE_KEY_CONTENT: {'Set' if hasattr(settings, 'BOX_PRIVATE_KEY_CONTENT') and settings.BOX_PRIVATE_KEY_CONTENT else 'Not set'}")
        
        # Make sure JWT_KEY_ID is a string
        jwt_key_id = str(settings.BOX_JWT_KEY_ID) if settings.BOX_JWT_KEY_ID else None
        
        # Try file path first if available (most reliable)
        if settings.BOX_PRIVATE_KEY_PATH and os.path.exists(settings.BOX_PRIVATE_KEY_PATH):
            logging.info(f"Using private key file from path: {settings.BOX_PRIVATE_KEY_PATH}")
            # Using private key file
            auth = JWTAuth(
                client_id=str(settings.BOX_CLIENT_ID) if settings.BOX_CLIENT_ID else None,
                client_secret=str(settings.BOX_CLIENT_SECRET) if settings.BOX_CLIENT_SECRET else None,
                enterprise_id=str(settings.BOX_ENTERPRISE_ID) if settings.BOX_ENTERPRISE_ID else None,
                jwt_key_id=jwt_key_id,
                rsa_private_key_file_sys_path=settings.BOX_PRIVATE_KEY_PATH,
                rsa_private_key_passphrase=settings.BOX_JWT_PRIVATE_KEY_PASSPHRASE.encode() if settings.BOX_JWT_PRIVATE_KEY_PASSPHRASE else None,
            )
        # Then try content if available
        elif hasattr(settings, 'BOX_PRIVATE_KEY_CONTENT') and settings.BOX_PRIVATE_KEY_CONTENT:
            # Process the content - convert \n back to real newlines
            logging.info("Using private key content from environment variable")
            key_content = settings.BOX_PRIVATE_KEY_CONTENT.replace('\\n', '\n')
            
            # For debugging, check the key format (without exposing full key)
            key_preview = key_content[:40] + "..." if len(key_content) > 40 else key_content
            logging.info(f"Key format check - starts with: {key_preview}")
            logging.info(f"Key length: {len(key_content)} characters")
            
            # Convert string key to bytes
            key_bytes = key_content.encode('utf-8')
            
            # Using private key content directly
            auth = JWTAuth(
                client_id=str(settings.BOX_CLIENT_ID) if settings.BOX_CLIENT_ID else None,
                client_secret=str(settings.BOX_CLIENT_SECRET) if settings.BOX_CLIENT_SECRET else None,
                enterprise_id=str(settings.BOX_ENTERPRISE_ID) if settings.BOX_ENTERPRISE_ID else None,
                jwt_key_id=jwt_key_id,
                rsa_private_key_data=key_bytes,
                rsa_private_key_passphrase=settings.BOX_JWT_PRIVATE_KEY_PASSPHRASE.encode() if settings.BOX_JWT_PRIVATE_KEY_PASSPHRASE else None,
            )
        else:
            # No key available
            raise ValueError("No private key available - either BOX_PRIVATE_KEY_PATH or BOX_PRIVATE_KEY_CONTENT must be set")

        # Get the authenticated client - this gives us the service account client directly
        client = Client(auth)
        
        # The following line should be used to get a client for a specific user
        # For now, we'll use the service account directly instead of getting current user
        # service_account_client = client.as_user(client.users.get_current_user())
        
        return client
    except Exception as e:
        logging.error(f"Error getting Box client: {e}", exc_info=True)
        raise e 