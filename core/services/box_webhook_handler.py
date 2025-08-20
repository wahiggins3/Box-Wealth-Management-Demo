"""
Box Webhook Handler

This module handles webhooks from Box to process documents when they are uploaded.
"""
import logging
import json
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .document_processing_service import DocumentProcessingService
from ..views import get_box_client

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def handle_box_webhook(request):
    """Handle incoming webhooks from Box.
    
    Args:
        request: HTTP request object
        
    Returns:
        HttpResponse: HTTP response
    """
    try:
        # Parse the webhook payload
        payload = json.loads(request.body)
        logger.info(f"Received Box webhook: {payload.get('trigger')}")
        
        # Validate webhook source
        # In production, you should validate webhook signatures
        
        # Process the event based on the trigger type
        if payload.get('trigger') == 'FILE.UPLOADED':
            return _handle_file_uploaded(payload)
        elif payload.get('trigger') == 'FILE.COPIED':
            return _handle_file_copied(payload)
        else:
            logger.info(f"Ignoring webhook with trigger: {payload.get('trigger')}")
            return JsonResponse({'status': 'ignored', 'message': 'Event type not handled'})
            
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def _handle_file_uploaded(payload):
    """Handle FILE.UPLOADED webhook.
    
    Args:
        payload: Webhook payload
        
    Returns:
        JsonResponse: JSON response
    """
    try:
        # Extract file information
        source = payload.get('source', {})
        if source.get('type') != 'file':
            return JsonResponse({'status': 'ignored', 'message': 'Source is not a file'})
            
        file_id = source.get('id')
        if not file_id:
            return JsonResponse({'status': 'error', 'message': 'File ID not found in payload'})
        
        # Get parent folder ID to check if it's an onboarding folder
        parent_folder_id = _get_parent_folder_id(payload)
        if not _is_onboarding_folder(parent_folder_id):
            logger.info(f"File {file_id} not in onboarding folder, skipping processing")
            return JsonResponse({'status': 'ignored', 'message': 'File not in onboarding folder'})
        
        # Process the document
        client = get_box_client()
        processing_service = DocumentProcessingService(client)
        result = processing_service.process_uploaded_document(file_id)
        
        if result.get('success'):
            return JsonResponse({
                'status': 'success',
                'message': result.get('message', 'Document processed successfully'),
                'details': result
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': result.get('message', 'Document processing failed'),
                'details': result
            }, status=500)
            
    except Exception as e:
        logger.error(f"Error handling file upload webhook: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

def _handle_file_copied(payload):
    """Handle FILE.COPIED webhook.
    
    Args:
        payload: Webhook payload
        
    Returns:
        JsonResponse: JSON response
    """
    # Similar logic to file_uploaded, but may have different requirements
    return _handle_file_uploaded(payload)  # For now, treat the same way

def _get_parent_folder_id(payload):
    """Extract parent folder ID from webhook payload.
    
    Args:
        payload: Webhook payload
        
    Returns:
        str: Parent folder ID or None
    """
    try:
        source = payload.get('source', {})
        parent = source.get('parent', {})
        return parent.get('id')
    except Exception:
        return None

def _is_onboarding_folder(folder_id):
    """Check if the folder is an onboarding folder.
    
    Args:
        folder_id: Box folder ID
        
    Returns:
        bool: True if it's an onboarding folder
    """
    if not folder_id:
        return False
        
    try:
        # Get the folder information from Box
        client = get_box_client()
        folder = client.folder(folder_id=folder_id).get()
        
        # Check if the folder name contains "Onboarding"
        # This is a simple check; you might want more sophisticated logic
        return "Onboarding" in folder.name
    except Exception as e:
        logger.error(f"Error checking folder type: {e}")
        return False 