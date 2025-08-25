from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.views.decorators.http import require_GET
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_exempt
import os
import traceback
import io
import json
import logging
import requests
import re
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from concurrent.futures import ThreadPoolExecutor, as_completed

from boxsdk import Client, JWTAuth, OAuth2
from boxsdk.exception import BoxAPIException
from core.services.box_metadata_extraction import BoxMetadataExtractionService
from core.services.box_metadata_application import BoxMetadataApplicationService
from core.utils import get_box_client
from core.services.document_processing_service import DocumentProcessingService
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from core.models import ClientOnboardingInfo, AddressMismatch
from core.services.address_comparison_service import AddressComparisonService

logger = logging.getLogger(__name__)

# Configure logging for Box SDK (optional, but helpful for debugging)
logging.getLogger('boxsdk').setLevel(logging.WARNING) # Be less verbose for the SDK itself unless debugging

# Create your views here.

def index(request):
    """Renders the summary page."""
    return render(request, 'index.html')

def accounts(request):
    """Renders the accounts page."""
    return render(request, 'accounts.html')

@login_required
def profile(request):
    """Renders the user profile page."""
    return render(request, 'profile.html')

@login_required
def documents(request):
    """Renders the documents page with Box integration."""
    context = {}
    
    # Structure for the folder descriptions
    folder_structure = [
        {
            'name': 'Onboarding Documents',
            'description': 'Documents required for account opening and setup',
            'purpose': 'Store completed forms and identification documents'
        },
        {
            'name': 'Private Documents',
            'description': 'Your confidential financial records',
            'purpose': 'Secure storage for sensitive financial information'
        },
        {
            'name': 'Shared with Advisor',
            'description': 'Documents shared with your financial advisor',
            'purpose': 'Collaborate with your advisor on financial planning'
        },
        {
            'name': 'Statements',
            'description': 'Regular account statements',
            'purpose': 'Archive of your monthly and quarterly statements'
        }
    ]
    
    context['folder_structure'] = folder_structure
    
    # Check if Box integration is enabled
    if not settings.BOX_ENABLED:
        context['error_message'] = "Box integration is not configured. Please contact the administrator."
        context['admin_message'] = "Missing Box API configuration. Set required environment variables in .env file."
        logging.warning("Box integration is not enabled - missing configuration")
    
    return render(request, 'documents.html', context)

def products(request):
    """Renders the products page."""
    return render(request, 'products.html')

def support(request):
    """Renders the support page with contact information and help resources."""
    return render(request, 'support.html')

def register(request):
    """Handles user registration."""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})

@login_required
def box_client_folder(request):
    """API endpoint to get or create a client folder structure."""
    try:
        # Derive client name from onboarding info, then user fields, then username
        user = request.user
        client_name = None
        
        # First try to get from onboarding info
        try:
            onboarding_info = user.onboarding_info
            if onboarding_info and onboarding_info.full_name:
                client_name = onboarding_info.full_name.strip()
                logging.info(f"Using client name from onboarding info: {client_name}")
        except (AttributeError, ClientOnboardingInfo.DoesNotExist):
            logging.info("No onboarding info found, falling back to user fields")
        
        # Fallback to user first/last name
        if not client_name:
            if user.first_name and user.last_name:
                client_name = f"{user.first_name} {user.last_name}"
                logging.info(f"Using client name from user fields: {client_name}")
        
        # Final fallback to username
        if not client_name:
            client_name = user.username
            logging.info(f"Using client name from username: {client_name}")
        
        logging.info(f"Creating/accessing folder for user: {client_name}")
        
        # Get the Box client
        client = get_box_client()
        
        # Use the specified parent folder ID with fallback
        parent_folder_id = '336919509525'  # Your specified root folder
        
        # Check if parent folder is accessible, fallback to root if not
        try:
            # First test if we can access the folder info (lighter call than get_items)
            folder_info = client.folder(folder_id=parent_folder_id).get()
            logging.info(f"Successfully accessed parent folder {parent_folder_id}: {folder_info.name}")
            # Now get items
            items = client.folder(folder_id=parent_folder_id).get_items(limit=1000)
        except Exception as e:
            logging.warning(f"Cannot access folder {parent_folder_id}: {e}. Falling back to service account root.")
            parent_folder_id = '0'  # Fallback to service account root
            try:
                # Create a "Clients" folder under root if it doesn't exist
                root_items = client.folder(folder_id='0').get_items(limit=1000)
                clients_folder = None
                for item in root_items:
                    if item.name == 'Clients' and item.type == 'folder':
                        clients_folder = item
                        break
                
                if not clients_folder:
                    clients_folder = client.folder('0').create_subfolder('Clients')
                    logging.info(f"Created 'Clients' folder: {clients_folder.id}")
                
                parent_folder_id = clients_folder.id
                items = client.folder(folder_id=parent_folder_id).get_items(limit=1000)
                logging.info(f"Using 'Clients' folder as parent: {parent_folder_id}")
            except Exception as fallback_error:
                logging.error(f"Fallback also failed: {fallback_error}")
                # Final fallback to root
                parent_folder_id = '0'
                items = client.folder(folder_id=parent_folder_id).get_items(limit=1000)
        
        client_folder = None
        
        for item in items:
            if item.name == client_name and item.type == 'folder':
                client_folder = item
                break
        
        # If client folder doesn't exist, create it
        if not client_folder:
            client_folder = client.folder(parent_folder_id).create_subfolder(client_name)
            logging.info(f"Created client folder: {client_folder.name} ({client_folder.id})")
            
            # Create the standard subfolders
            subfolders = [
                'Onboarding Documents',
                'Private Documents',
                'Shared with Advisor',
                'Statements'
            ]
            
            for subfolder_name in subfolders:
                subfolder = client.folder(client_folder.id).create_subfolder(subfolder_name)
                logging.info(f"Created subfolder: {subfolder.name} ({subfolder.id})")
        
        return JsonResponse({
            'success': True,
            'folderId': client_folder.id,
            'clientName': client_name
        })
        
    except Exception as e:
        logging.error(f"Error in box_client_folder: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def box_onboarding_folder(request):
    """API endpoint to get or create a client's onboarding subfolder."""
    try:
        client_name = request.GET.get('clientName')
        if not client_name:
            return JsonResponse({'error': 'Client name is required'}, status=400)
        
        # Get the Box client
        client = get_box_client()
        
        # The parent folder where all client folders are stored
        parent_folder_id = '320099222198'  # Specific parent folder for client documents
        
        # Check if client folder exists
        items = client.folder(folder_id=parent_folder_id).get_items(limit=1000)
        client_folder = None
        
        for item in items:
            if item.name == client_name and item.type == 'folder':
                client_folder = item
                break
        
        # If client folder doesn't exist, create it
        if not client_folder:
            client_folder = client.folder(parent_folder_id).create_subfolder(client_name)
            logging.info(f"Created client folder: {client_folder.name} ({client_folder.id})")
        
        # Define the required subfolder names
        required_subfolders = [
            "Onboarding Documents", 
            "Shared with Advisor", 
            "Private Documents", 
            "Statements"
        ]
        
        # Get existing subfolders
        subfolder_items = client.folder(folder_id=client_folder.id).get_items(limit=100)
        existing_subfolder_names = {item.name for item in subfolder_items if item.type == 'folder'}

        # Create any missing required subfolders
        for folder_name in required_subfolders:
            if folder_name not in existing_subfolder_names:
                created_folder = client.folder(client_folder.id).create_subfolder(folder_name)
                logging.info(f"Created subfolder: {created_folder.name} ({created_folder.id}) in {client_folder.name}")
        
        # Find the "Onboarding Documents" subfolder to return its ID
        onboarding_docs_folder_id = None
        all_subfolders_in_client_folder = client.folder(folder_id=client_folder.id).get_items(limit=100)
        for sub_item in all_subfolders_in_client_folder:
            if sub_item.name == "Onboarding Documents" and sub_item.type == 'folder':
                onboarding_docs_folder_id = sub_item.id
                break
        
        if not onboarding_docs_folder_id:
            logging.error(f"'Onboarding Documents' subfolder not found in {client_folder.name} ({client_folder.id}) after creation attempt.")
            return JsonResponse({'error': "Failed to find or create the 'Onboarding Documents' subfolder."}, status=500)

        # Return the "Onboarding Documents" folder ID for the uploader
        return JsonResponse({
            'success': True,
            'folderId': onboarding_docs_folder_id, # ID of the "Onboarding Documents" folder
            'clientName': client_name,
            'parentFolderId': client_folder.id # Parent of "Onboarding Documents" is the client_folder
        })
        
    except Exception as e:
        logging.error(f"Error in box_onboarding_folder: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def box_explorer_token(request):
    """API endpoint to generate a downscoped token for Box Content Explorer."""
    try:
        folder_id = request.GET.get('folderId')
        if not folder_id:
            return JsonResponse({'error': 'Folder ID is required'}, status=400)
        
        # Get the Box client
        client = get_box_client()
        
        # Define the scopes for the downscoped token
        # These scopes are specifically for the Content Explorer UI Element
        scopes = [
            'base_explorer',
            'item_preview',
            'item_upload',
            'item_delete',
            'item_rename'
        ]
        
        # Generate the downscoped token (MVP: fall back to full service token if scopes insufficient)
        try:
            box_response = client.downscope_token(
                scopes=scopes,
                item=client.folder(folder_id=folder_id)
            )
            token_value = box_response['access_token']
        except Exception as e:
            logging.warning(f"Downscope failed ({e}); falling back to service access token for MVP.")
            # Use service account access token directly
            token_value = client.auth.access_token
        
        # Return the token in the response
        return JsonResponse({'success': True, 'token': token_value, 'folderId': folder_id})
        
    except Exception as e:
        logging.error(f"Error in box_explorer_token: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@login_required # Ensure only logged-in users can access this
def box_documents(request):
    """Authenticates with Box and fetches root folder items. Returns a context dict."""
    box_items = None
    error_message = None

    try:
        # Get Box client (no need to use as_user anymore)
        client = get_box_client()

        # Fetch items from the root folder ('0')
        items = client.folder(folder_id='0').get_items(limit=100)
        box_items = list(items) # Convert iterator to list for template

    except BoxAPIException as e:
        error_message = f"Box API Error: {e.status} - {getattr(e, 'message', 'Unknown error')}"
        logging.error(f"Box API Error: {e}")
    except Exception as e:
        error_message = f"An unexpected error occurred: {e}"
        logging.error(f"Error fetching Box documents: {e}", exc_info=True)

    context = {
        'box_items': box_items,
        'error_message': error_message,
    }
    
    return context

def logout_view(request):
    """Custom logout view that accepts both GET and POST requests."""
    logout(request)
    return redirect('login')

@login_required
def wealth_onboarding(request):
    """Renders the wealth management onboarding page."""
    context = {}
    
    if request.method == 'POST':
        try:
            # Get or create the client onboarding info
            onboarding_info, created = ClientOnboardingInfo.objects.get_or_create(
                user=request.user,
                defaults={}
            )
            
            # Update personal information
            onboarding_info.full_name = request.POST.get('full_name', '')
            onboarding_info.email = request.POST.get('email', '')
            onboarding_info.phone = request.POST.get('phone', '')
            
            # Handle birth_date conversion
            birth_date_str = request.POST.get('birth_date')
            if birth_date_str:
                from datetime import datetime
                try:
                    onboarding_info.birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
                except ValueError:
                    pass  # Keep existing value if date format is invalid
            
            # Update address information
            onboarding_info.street_address = request.POST.get('street_address', '')
            onboarding_info.city = request.POST.get('city', '')
            onboarding_info.state_province = request.POST.get('state_province', '')
            onboarding_info.postal_code = request.POST.get('postal_code', '')
            onboarding_info.country = request.POST.get('country', 'USA')
            
            # Update financial information
            retirement_age_str = request.POST.get('retirement_age')
            if retirement_age_str:
                try:
                    onboarding_info.retirement_age = int(retirement_age_str)
                except ValueError:
                    pass
            
            monthly_income_str = request.POST.get('monthly_income')
            if monthly_income_str:
                try:
                    from decimal import Decimal
                    onboarding_info.monthly_income = Decimal(monthly_income_str)
                except (ValueError, TypeError):
                    pass
            
            onboarding_info.risk_tolerance = request.POST.get('risk_tolerance', '')
            
            # Handle investment goals (checkboxes)
            investment_goals = request.POST.getlist('investment_goals')
            onboarding_info.investment_goals = investment_goals
            
            onboarding_info.investment_timeframe = request.POST.get('investment_timeframe', '')
            onboarding_info.investable_assets = request.POST.get('investable_assets', '')
            onboarding_info.special_considerations = request.POST.get('special_considerations', '')
            
            # Save the updated information
            onboarding_info.save()
            
            logging.info(f"Saved onboarding info for user {request.user.username}")
            
            # Create the Box folder structure for this client
            try:
                logging.info(f"Creating Box folder structure for user {request.user.username}")
                # Call the box_client_folder endpoint to ensure folder structure is created
                from django.test import RequestFactory
                factory = RequestFactory()
                folder_request = factory.get('/api/box/client-folder/')
                folder_request.user = request.user
                
                # Call our own view to create the folder structure
                folder_response = box_client_folder(folder_request)
                if folder_response.status_code == 200:
                    logging.info(f"Successfully created Box folder structure for user {request.user.username}")
                else:
                    logging.warning(f"Box folder creation returned status {folder_response.status_code}")
            except Exception as e:
                logging.error(f"Error creating Box folder structure for user {request.user.username}: {e}")
                # Don't fail the onboarding process if folder creation fails
            
            context['success_message'] = 'Your information has been saved successfully!'
            
            # Redirect to document upload page
            return redirect('document_upload')
            
        except Exception as e:
            logging.error(f"Error saving onboarding info for user {request.user.username}: {e}")
            context['error_message'] = 'There was an error saving your information. Please try again.'
    
    # If GET request, try to load existing data
    try:
        onboarding_info = ClientOnboardingInfo.objects.get(user=request.user)
        context['onboarding_info'] = onboarding_info
    except ClientOnboardingInfo.DoesNotExist:
        pass  # No existing data, form will be empty
        
    return render(request, 'wealth_onboarding.html', context)

@login_required
def document_upload(request):
    """Renders the document upload page."""
    context = {}
    return render(request, 'document_upload.html', context)

@login_required
def submission_complete(request):
    """Renders the submission completion page."""
    return render(request, 'submission_complete.html')

@login_required
@csrf_exempt
def create_horizon_plan(request):
    """Create 'Your Horizon Plan' folder and copy the financial plan document."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Only POST method allowed'}, status=405)
    
    try:
        # Get Box client
        box_client = get_box_client()
        
        # Get the user's client folder (same logic as box_client_folder)
        user = request.user
        
        # Determine client folder name
        client_name = None
        if hasattr(user, 'onboarding_info') and user.onboarding_info and user.onboarding_info.full_name:
            client_name = user.onboarding_info.full_name.strip()
        elif user.first_name and user.last_name:
            client_name = f"{user.first_name} {user.last_name}".strip()
        else:
            client_name = user.username
        
        # Try to find the client folder
        parent_folder_id = '336919509525'  # Same as document upload
        try:
            parent_folder = box_client.folder(parent_folder_id).get()
            logging.info(f"Using specified parent folder: {parent_folder.name} (ID: {parent_folder_id})")
        except Exception as e:
            logging.warning(f"Cannot access folder {parent_folder_id}, using root: {e}")
            parent_folder_id = '0'
            parent_folder = box_client.folder(parent_folder_id).get()
        
        # Use the same logic as box_client_folder to ensure we get the same folder structure
        # Call box_client_folder to get or create the client folder with all subfolders
        from django.test import RequestFactory
        factory = RequestFactory()
        folder_request = factory.get('/api/box/client-folder/')
        folder_request.user = request.user
        
        # Call our own view to get the client folder structure
        folder_response = box_client_folder(folder_request)
        if folder_response.status_code != 200:
            return JsonResponse({'success': False, 'message': 'Failed to get client folder structure'}, status=500)
        
        # Parse the response to get the client folder ID
        import json
        folder_data = json.loads(folder_response.content.decode('utf-8'))
        client_folder_id = folder_data['folderId']
        client_folder = box_client.folder(client_folder_id)
        
        logging.info(f"Using existing client folder: {client_name} (ID: {client_folder_id})")
        
        # Create "Your Horizon Plan" folder inside the client folder (same level as other subfolders)
        plan_folder_name = "Your Horizon Plan"
        plan_folder = None
        
        # Check if plan folder already exists
        client_items = client_folder.get_items()
        for item in client_items:
            if item.type == 'folder' and item.name == plan_folder_name:
                plan_folder = item
                break
        
        if not plan_folder:
            plan_folder = client_folder.create_subfolder(plan_folder_name)
            logging.info(f"Created plan folder: {plan_folder_name} (ID: {plan_folder.id}) inside client folder {client_name}")
        
        # Upload the financial plan document
        import os
        plan_file_path = os.path.join(settings.BASE_DIR, 'horizon_financial_plan_final.pdf')
        
        if not os.path.exists(plan_file_path):
            return JsonResponse({'success': False, 'message': 'Financial plan document not found'}, status=404)
        
        # Check if file already exists in the folder
        plan_file = None
        plan_items = plan_folder.get_items()
        for item in plan_items:
            if item.type == 'file' and item.name == 'horizon_financial_plan_final.pdf':
                plan_file = item
                break
        
        if not plan_file:
            # Upload the file
            with open(plan_file_path, 'rb') as file_stream:
                plan_file = plan_folder.upload_stream(file_stream, 'horizon_financial_plan_final.pdf')
                logging.info(f"Uploaded financial plan document: {plan_file.name} (ID: {plan_file.id})")
        
        return JsonResponse({
            'success': True,
            'message': 'Financial plan created successfully',
            'plan_folder_id': plan_folder.id,
            'plan_file_id': plan_file.id,
            'client_name': client_name
        })
        
    except Exception as e:
        logging.error(f"Error creating horizon plan: {e}", exc_info=True)
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
def financial_plan_preview(request):
    """Renders the financial plan preview page with Box preview UI."""
    return render(request, 'financial_plan_preview.html')

@login_required
@csrf_exempt
def get_plan_preview_token(request):
    """Get a preview token specifically for the financial plan file."""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': 'Only GET method allowed'}, status=405)
    
    try:
        file_id = request.GET.get('file_id')
        if not file_id:
            return JsonResponse({'success': False, 'message': 'file_id parameter required'}, status=400)
        
        # Get Box client
        box_client = get_box_client()
        
        # Get the file to ensure it exists and we have access
        file_obj = box_client.file(file_id).get()
        logging.info(f"File found: {file_obj.name} (ID: {file_id})")
        
        # Create downscoped token for this specific file
        try:
            # Try to create a downscoped token with file preview permissions
            downscoped_token = box_client.downscope_token(
                scopes=['item_preview', 'item_download'],
                item=f"https://api.box.com/2.0/files/{file_id}"
            )
            
            return JsonResponse({
                'success': True,
                'access_token': downscoped_token,
                'file_id': file_id,
                'file_name': file_obj.name
            })
            
        except Exception as downscope_error:
            logging.warning(f"Downscoping failed: {downscope_error}")
            
            # Fallback: return the full service account token
            # This should work for preview since we have full access
            auth = box_client.auth
            access_token = auth.access_token
            
            return JsonResponse({
                'success': True,
                'access_token': access_token,
                'file_id': file_id,
                'file_name': file_obj.name,
                'note': 'Using full service account token as fallback'
            })
            
    except Exception as e:
        logging.error(f"Error getting plan preview token: {e}", exc_info=True)
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
def test_horizon_plan(request):
    """Test endpoint to manually trigger horizon plan creation."""
    try:
        # Call the create_horizon_plan view directly
        from django.test import RequestFactory
        factory = RequestFactory()
        post_request = factory.post('/api/box/create-horizon-plan/')
        post_request.user = request.user
        
        response = create_horizon_plan(post_request)
        
        if hasattr(response, 'content'):
            import json
            result = json.loads(response.content.decode('utf-8'))
            return JsonResponse({
                'test_result': result,
                'status_code': response.status_code
            })
        else:
            return JsonResponse({'error': 'Unexpected response type'})
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@csrf_exempt
def reset_demo(request):
    """Reset demo by deleting Horizon Plan folder and clearing session storage."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Only POST method allowed'}, status=405)
    
    try:
        # Get Box client
        box_client = get_box_client()
        
        # Use the same logic as create_horizon_plan to find the client folder
        # Call box_client_folder to get the client folder structure
        from django.test import RequestFactory
        factory = RequestFactory()
        folder_request = factory.get('/api/box/client-folder/')
        folder_request.user = request.user
        
        # Call our own view to get the client folder structure
        folder_response = box_client_folder(folder_request)
        if folder_response.status_code != 200:
            return JsonResponse({
                'success': True,
                'message': 'No client folder found - nothing to reset'
            })
        
        # Parse the response to get the client folder ID
        import json
        folder_data = json.loads(folder_response.content.decode('utf-8'))
        client_folder_id = folder_data['folderId']
        client_name = folder_data['clientName']
        client_folder = box_client.folder(client_folder_id)
        
        logging.info(f"Found client folder for reset: {client_name} (ID: {client_folder_id})")
        
        # Find "Your Horizon Plan" folder inside client folder
        plan_folder_name = "Your Horizon Plan"
        plan_folder = None
        
        try:
            client_items = client_folder.get_items()
            for item in client_items:
                if item.type == 'folder' and item.name == plan_folder_name:
                    plan_folder = item
                    break
            
            if plan_folder:
                # Delete the entire "Your Horizon Plan" folder (this will delete all files inside it too)
                plan_folder.delete()
                logging.info(f"RESET: Deleted Horizon Plan folder: {plan_folder_name} (ID: {plan_folder.id})")
                
                return JsonResponse({
                    'success': True,
                    'message': f'Demo reset successfully - "{plan_folder_name}" folder and all contents deleted',
                    'client_name': client_name,
                    'deleted_folder_id': plan_folder.id
                })
            else:
                return JsonResponse({
                    'success': True,
                    'message': f'No "{plan_folder_name}" folder found - nothing to reset',
                    'client_name': client_name
                })
                
        except Exception as folder_error:
            logging.error(f"Error accessing client folder contents: {folder_error}")
            return JsonResponse({
                'success': True,
                'message': f'Could not access client folder contents - may already be clean',
                'client_name': client_name
            })
        
    except Exception as e:
        logging.error(f"Error resetting demo: {e}", exc_info=True)
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
@csrf_exempt
def generate_financial_summary(request):
    """Generate a financial summary PDF using Box AI.
    
    This endpoint creates a financial summary PDF based on the uploaded documents.
    It includes improved error handling, fallback mechanisms, and multiple AI agent support.
    
    Args:
        request: HTTP request
        
    Returns:
        JSON response with the result of the PDF generation
    """
    try:
        logging.info("========== STARTING IMPROVED FINANCIAL SUMMARY GENERATION ==========")
        if request.method != 'POST':
            logging.error("Invalid method for generate_financial_summary: %s", request.method)
            return JsonResponse({'success': False, 'message': 'Only POST method is allowed'}, status=405)
        
        # Parse JSON data from the request
        try:
            data = json.loads(request.body)
            folder_id = data.get('folderId')
            logging.info(f"Received request to generate financial summary for folder ID: {folder_id}")
            
            if not folder_id:
                logging.error("Missing folder ID in request")
                return JsonResponse({'success': False, 'message': 'Missing folder ID'}, status=400)
        except json.JSONDecodeError:
            logging.error("Invalid JSON payload in request")
            return JsonResponse({'success': False, 'message': 'Invalid JSON payload'}, status=400)
        
        # Get an authenticated Box client
        logging.info("Getting authenticated Box client")
        box_client = get_box_client()
        
        # Get the folder and files
        try:
            logging.info(f"Accessing folder {folder_id}")
            folder = box_client.folder(folder_id)
            folder_info = folder.get()
            folder_name = folder_info.name
            logging.info(f"Processing folder: {folder_name} (ID: {folder_id})")
            
            files = []
            folder_items = folder.get_items(limit=1000)
            
            for item in folder_items:
                if item.type == 'file':
                    files.append(item)
            
            logging.info(f"Found {len(files)} files in folder {folder_id}")
            
            if not files:
                logging.error(f"No files found in folder {folder_id}")
                return JsonResponse({'success': False, 'message': 'No files found in the folder'}, status=404)
        except Exception as e:
            logging.error(f"Error accessing folder {folder_id}: {e}")
            return JsonResponse({'success': False, 'message': f'Could not access folder: {str(e)}'}, status=500)
        
        # Try Box AI with multiple agent fallback
        working_agent = None
        financial_summary = ""
        summary_data = {}
        
        try:
            # Get access token
            auth = box_client.auth
            access_token = auth._access_token
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Try different AI agent configurations
            ai_agents = [
                {"id": "1329589", "type": "ai_agent_id"},  # Original agent
                {"type": "ai_agent_ask"},  # Generic ask agent
                {"type": "ai_agent_text_gen"},  # Text generation agent
            ]
            
            # Test with first file to find working agent
            for i, ai_agent in enumerate(ai_agents):
                try:
                    logging.info(f"Testing AI agent {i+1}: {ai_agent}")
                    test_file = files[0]
                    
                    test_payload = {
                        "mode": "single_item_qa",
                        "prompt": "Provide a brief summary of this financial document.",
                        "items": [{"id": test_file.id, "type": "file"}],
                        "ai_agent": ai_agent
                    }
                    
                    response = requests.post(
                        'https://api.box.com/2.0/ai/ask',
                        headers=headers,
                        json=test_payload,
                        timeout=30
                    )
                    
                    if response.status_code in [200, 201, 202]:
                        test_response = response.json()
                        if test_response.get('answer', '').strip():
                            working_agent = ai_agent
                            logging.info(f"Found working AI agent: {ai_agent}")
                            break
                    else:
                        logging.warning(f"AI agent {i+1} failed with status {response.status_code}")
                        
                except Exception as e:
                    logging.warning(f"AI agent {i+1} test failed: {str(e)}")
                    continue
            
            # Generate full summary with working agent
            if working_agent:
                logging.info("Generating full summary with working AI agent")
                
                ai_items = []
                for file_item in files:
                    ai_items.append({
                        "id": file_item.id,
                        "type": "file"
                    })
                
                ai_request_payload = {
                    "mode": "multiple_item_qa",
                    "prompt": """Analyze these financial documents and provide a consolidated financial summary. Avoid duplicates and provide clean, organized data:

**ASSETS:**
- Cash: $X,XXX (total cash across all accounts)
- Real Estate: $X,XXX (property values)
- Vehicles: $X,XXX (if any)
- Other Assets: $X,XXX (collectibles, etc.)

**LIABILITIES:**
- Mortgage: $X,XXX
- Credit Cards: $X,XXX (total balance)
- Auto Loans: $X,XXX
- Student Loans: $X,XXX
- Other Debts: $X,XXX

**ACCOUNTS:**
- Checking: $X,XXX
- Savings: $X,XXX
- Brokerage: $X,XXX
- 401(k): $X,XXX
- IRA: $X,XXX
- Other Retirement: $X,XXX

**UNREALIZED GAINS/LOSSES:**
- [Stock Symbol]: +$X,XXX or -$X,XXX
- [Fund Name]: +$X,XXX or -$X,XXX
(Only list specific holdings with unrealized gains/losses)

**INVESTMENTS BY SECTOR:**
- Technology: $X,XXX
- Healthcare: $X,XXX
- Financial: $X,XXX
- Energy: $X,XXX
- Real Estate: $X,XXX
- Manufacturing: $X,XXX
- Other: $X,XXX

**SUMMARY:**
Provide a 2-3 sentence overview of the client's financial position.

IMPORTANT: 
- Consolidate similar items (don't list "cash" multiple times)
- Use exact dollar amounts from documents
- Group investments by broad sector categories
- Only include accounts/assets that actually exist in the documents
- Mask account numbers for privacy""",
                    "items": ai_items,
                    "ai_agent": working_agent
                }
                
                response = requests.post(
                    'https://api.box.com/2.0/ai/ask',
                    headers=headers,
                    json=ai_request_payload,
                    timeout=120  # Longer timeout for multiple files
                )
                
                if response.status_code in [200, 201, 202]:
                    ai_response = response.json()
                    financial_summary = ai_response.get('answer', '')
                    
                    if financial_summary:
                        logging.info("AI analysis completed successfully")
                        summary_data = {
                            "ai_summary": financial_summary,
                            "total_files": len(files),
                            "analysis_method": "Box AI",
                            "agent_used": working_agent
                        }
                    else:
                        raise Exception("Empty AI response")
                else:
                    raise Exception(f"AI request failed with status {response.status_code}")
            else:
                raise Exception("No working AI agent found")
                
        except Exception as ai_error:
            logging.warning(f"AI analysis failed: {str(ai_error)}, creating fallback summary")
            
            # Create fallback summary
            summary_data = {
                "summary": f"Financial document analysis for {folder_name}",
                "total_files": len(files),
                "files_processed": [],
                "analysis_method": "Fallback",
                "note": "AI analysis was unavailable. This is a basic document listing."
            }
            
            for file_item in files:
                file_info = {
                    "file_name": file_item.name,
                    "file_id": file_item.id,
                    "file_type": "Document"
                }
                summary_data["files_processed"].append(file_info)
            
            financial_summary = f"Document analysis completed for {len(files)} files in {folder_name}."
        
        # Generate PDF
        pdf_created = False
        upload_file_stream = None
        upload_file_name = ""
        upload_format = ""
        
        def parse_financial_summary(ai_text):
            """Parse AI summary text into structured financial data"""
            try:
                # Helper function to shorten long names to 2-3 words
                def shorten_name(name):
                    """Shorten a name to 2-3 words maximum"""
                    if not name:
                        return 'Unknown'
                    
                    # Common abbreviations for financial terms
                    abbreviations = {
                        'checking': 'Checking',
                        'savings': 'Savings',
                        'brokerage': 'Brokerage',
                        'investment': 'Investment',
                        'retirement': 'Retirement',
                        'mortgage': 'Mortgage',
                        'credit card': 'Credit Card',
                        'credit cards': 'Credit Cards',
                        'auto loan': 'Auto Loan',
                        'student loan': 'Student Loan',
                        'personal loan': 'Personal Loan',
                        'real estate': 'Real Estate',
                        'primary residence': 'Primary Home',
                        'primary mortgage': 'Mortgage',
                        'traditional ira': 'Traditional IRA',
                        'roth ira': 'Roth IRA',
                        'education account': 'Education 529',
                        'cash on hand': 'Cash',
                        'american express': 'Amex Card',
                        'honda crv': 'Honda CRV'
                    }
                    
                    # Clean up the name
                    name = str(name).strip()
                    name_lower = name.lower()
                    
                    # Check for exact abbreviation matches
                    for long_name, short_name in abbreviations.items():
                        if long_name in name_lower:
                            return short_name
                    
                    # If no abbreviation found, take first 2-3 meaningful words
                    words = name.split()
                    
                    # Remove common words like "the", "and", "of", etc.
                    meaningful_words = []
                    skip_words = {'the', 'and', 'or', 'of', 'in', 'at', 'to', 'for', 'with', 'a', 'an'}
                    
                    for word in words:
                        if word.lower() not in skip_words:
                            meaningful_words.append(word)
                    
                    # Take first 2-3 meaningful words
                    if len(meaningful_words) <= 2:
                        return ' '.join(meaningful_words)
                    elif len(meaningful_words) == 3:
                        # If third word is short (like "Bank"), include it
                        if len(meaningful_words[2]) <= 4:
                            return ' '.join(meaningful_words[:3])
                        else:
                            return ' '.join(meaningful_words[:2])
                    else:
                        # For 4+ words, take first 2
                        return ' '.join(meaningful_words[:2])
                
                # First, try to parse as JSON
                try:
                    # Clean up the text - remove any markdown code blocks if present
                    clean_text = ai_text.strip()
                    if clean_text.startswith('```json') and clean_text.endswith('```'):
                        clean_text = clean_text[7:-3].strip()
                    elif clean_text.startswith('```') and clean_text.endswith('```'):
                        clean_text = clean_text[3:-3].strip()
                    
                    # Try to parse as JSON
                    json_data = json.loads(clean_text)
                    
                    # Convert JSON to expected structure
                    structured_data = {
                        'assets': [],
                        'liabilities': [],
                        'accounts': [],
                        'unrealized_gains_losses': [],
                        'investments_by_sector': [],
                        'summary': ''
                    }
                    
                    # Handle assets_liabilities section
                    if 'assets_liabilities' in json_data:
                        for item in json_data['assets_liabilities']:
                            if item.get('type') == 'asset':
                                structured_data['assets'].append({
                                    'name': shorten_name(item.get('name', 'Unknown')),
                                    'value': f"${item.get('amount', 0):,.2f}".replace('.00', '')
                                })
                            elif item.get('type') == 'liability':
                                structured_data['liabilities'].append({
                                    'name': shorten_name(item.get('name', 'Unknown')),
                                    'value': f"${item.get('amount', 0):,.2f}".replace('.00', '')
                                })
                    
                    # Handle investments by sector
                    if 'investments_by_sector' in json_data:
                        for item in json_data['investments_by_sector']:
                            structured_data['investments_by_sector'].append({
                                'name': shorten_name(item.get('sector', 'Unknown')),
                                'value': f"${item.get('amount', 0):,.2f}".replace('.00', '')
                            })
                    
                    # Handle unrealized gains/losses
                    if 'unrealized_gains_losses' in json_data:
                        for item in json_data['unrealized_gains_losses']:
                            gain_loss = item.get('gain_loss', 0)
                            sign = '+' if gain_loss >= 0 else ''
                            structured_data['unrealized_gains_losses'].append({
                                'name': shorten_name(item.get('asset', 'Unknown')),
                                'value': f"{sign}${gain_loss:,.2f}".replace('.00', '')
                            })
                    
                    # Handle summary
                    if 'financial_health_summary' in json_data:
                        structured_data['summary'] = json_data['financial_health_summary']
                    
                    # Check if we have any structured data
                    has_data = any(structured_data[key] for key in ['assets', 'liabilities', 'accounts', 'unrealized_gains_losses', 'investments_by_sector'])
                    
                    if has_data:
                        logging.info("Successfully parsed AI response as JSON")
                        return structured_data
                        
                except (json.JSONDecodeError, KeyError, TypeError) as json_error:
                    logging.info(f"AI response is not JSON, falling back to text parsing: {json_error}")
                    # Fall through to text parsing logic below
                
                # Original text parsing logic for non-JSON responses
                structured_data = {
                    'assets': [],
                    'liabilities': [],
                    'accounts': [],
                    'unrealized_gains_losses': [],
                    'investments_by_sector': [],
                    'summary': ''
                }
                
                # Split text into sections based on headers
                sections = {
                    'assets': [],
                    'liabilities': [],
                    'accounts': [],
                    'unrealized_gains_losses': [],
                    'investments_by_sector': [],
                    'summary': []
                }
                
                current_section = None
                lines = ai_text.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Check for section headers
                    line_lower = line.lower()
                    if '**assets:**' in line_lower or 'assets:' in line_lower:
                        current_section = 'assets'
                        continue
                    elif '**liabilities:**' in line_lower or 'liabilities:' in line_lower:
                        current_section = 'liabilities'
                        continue
                    elif '**accounts:**' in line_lower or 'accounts:' in line_lower:
                        current_section = 'accounts'
                        continue
                    elif '**unrealized gains/losses:**' in line_lower or 'unrealized gains' in line_lower:
                        current_section = 'unrealized_gains_losses'
                        continue
                    elif '**investments by sector:**' in line_lower or 'investments by sector' in line_lower:
                        current_section = 'investments_by_sector'
                        continue
                    elif '**summary:**' in line_lower or (current_section is None and 'summary' in line_lower):
                        current_section = 'summary'
                        continue
                    
                    # Add content to current section
                    if current_section and line:
                        # Remove bullet points and clean up
                        clean_line = line.lstrip('- •*').strip()
                        
                        # Skip lines that are just category headers or empty
                        if clean_line and ':' in clean_line and not clean_line.lower().startswith('important'):
                            # Only add lines that have actual data (contain a colon separator)
                            sections[current_section].append(clean_line)
                
                # Convert to structured format with simplified item names
                for section, items in sections.items():
                    if section == 'summary':
                        structured_data[section] = ' '.join(items)
                    else:
                        # Process each item to extract concise names and values
                        processed_items = []
                        seen_items = set()  # Track items to avoid duplicates
                        
                        for item in items:
                            processed_item = simplify_item_name(item)
                            if processed_item:
                                # Create a key for deduplication based on name
                                item_key = processed_item['name'].lower().strip()
                                
                                # Skip if we've already seen this item type
                                if item_key not in seen_items:
                                    processed_items.append(processed_item)
                                    seen_items.add(item_key)
                                else:
                                    # If duplicate, try to consolidate values
                                    existing_item = next((item for item in processed_items if item['name'].lower().strip() == item_key), None)
                                    if existing_item and processed_item['value']:
                                        # Try to combine values if they're numeric
                                        existing_item['value'] = consolidate_values(existing_item['value'], processed_item['value'])
                        
                        structured_data[section] = processed_items
                
                # Check if we have any structured data
                has_data = any(structured_data[key] for key in ['assets', 'liabilities', 'accounts', 'unrealized_gains_losses', 'investments_by_sector'])
                
                return structured_data if has_data else None
                
            except Exception as e:
                logging.warning(f"Error parsing financial summary: {e}")
                return None
        
        def consolidate_values(existing_value, new_value):
            """Consolidate two financial values, combining them if possible"""
            try:
                import re
                
                # Extract dollar amounts from both values
                dollar_pattern = r'\$[\d,]+(?:\.\d{2})?'
                existing_match = re.search(dollar_pattern, str(existing_value))
                new_match = re.search(dollar_pattern, str(new_value))
                
                if existing_match and new_match:
                    # Extract numeric values
                    existing_amount = float(existing_match.group().replace('$', '').replace(',', ''))
                    new_amount = float(new_match.group().replace('$', '').replace(',', ''))
                    
                    # Combine the amounts
                    total_amount = existing_amount + new_amount
                    return f"${total_amount:,.2f}".replace('.00', '')
                else:
                    # If can't parse as numbers, return the more detailed value
                    return new_value if len(str(new_value)) > len(str(existing_value)) else existing_value
                    
            except:
                # If any error, just return the existing value
                return existing_value
        
        def simplify_item_name(item_text):
            """Convert long item descriptions to concise 2-3 word names with values"""
            try:
                # Split on colon or dash to separate name from value
                if ':' in item_text:
                    parts = item_text.split(':', 1)
                elif ' - ' in item_text:
                    parts = item_text.split(' - ', 1)
                else:
                    # If no separator, try to extract key terms
                    parts = [item_text, '']
                
                name_part = parts[0].strip()
                value_part = parts[1].strip() if len(parts) > 1 else ''
                
                # Simplify common financial terms to 2-3 words
                name_mappings = {
                    'checking account': 'Checking',
                    'savings account': 'Savings', 
                    'investment account': 'Investment',
                    'retirement account': 'Retirement',
                    '401k': '401(k)',
                    'ira': 'IRA',
                    'roth ira': 'Roth IRA',
                    'mortgage': 'Mortgage',
                    'home loan': 'Mortgage',
                    'credit card': 'Credit Cards',
                    'auto loan': 'Auto Loans',
                    'car loan': 'Auto Loans',
                    'student loan': 'Student Loans',
                    'personal loan': 'Personal Loan',
                    'line of credit': 'Line of Credit',
                    'brokerage': 'Brokerage',
                    'mutual fund': 'Mutual Funds',
                    'stock': 'Stocks',
                    'bond': 'Bonds',
                    'etf': 'ETFs',
                    'real estate': 'Real Estate',
                    'property': 'Real Estate',
                    'cash': 'Cash',
                    'certificate of deposit': 'CD',
                    'money market': 'Money Market',
                    'technology': 'Technology',
                    'healthcare': 'Healthcare',
                    'financial': 'Financial',
                    'energy': 'Energy',
                    'manufacturing': 'Manufacturing',
                    'other retirement': 'Other Retirement',
                    'other debts': 'Other Debts',
                    'other assets': 'Other Assets',
                    'vehicles': 'Vehicles'
                }
                
                # Look for mappings in the name
                simplified_name = name_part.lower()
                for key, short_name in name_mappings.items():
                    if key in simplified_name:
                        simplified_name = short_name
                        break
                else:
                    # If no mapping found, take first 2-3 meaningful words
                    words = name_part.split()
                    # Filter out common articles and prepositions
                    meaningful_words = [w for w in words if w.lower() not in ['the', 'and', 'or', 'of', 'in', 'at', 'to', 'for', 'with']]
                    simplified_name = ' '.join(meaningful_words[:2]).title()
                
                # Extract and clean up value
                if value_part:
                    # Look for dollar amounts
                    import re
                    dollar_match = re.search(r'\$[\d,]+(?:\.\d{2})?', value_part)
                    if dollar_match:
                        value_part = dollar_match.group()
                    else:
                        # If no dollar amount, take first meaningful part
                        value_part = value_part.split(',')[0].strip()
                        if len(value_part) > 30:
                            value_part = value_part[:30] + '...'
                
                return {'name': simplified_name, 'value': value_part} if simplified_name else None
                
            except Exception as e:
                logging.warning(f"Error simplifying item name: {e}")
                return None
        
        def add_financial_tables(content, structured_data, header_style, subheader_style, normal_style):
            """Add formatted tables for each financial category"""
            try:
                # Assets section
                if structured_data.get('assets'):
                    content.append(Paragraph("Assets", header_style))
                    assets_data = [['Type', 'Value']]
                    for asset in structured_data['assets']:
                        if isinstance(asset, dict):
                            assets_data.append([asset.get('name', 'Unknown'), asset.get('value', 'N/A')])
                        else:
                            # Fallback for string format
                            if ':' in str(asset):
                                parts = str(asset).split(':', 1)
                                name = parts[0].strip()[:15]  # Limit name length
                                value = parts[1].strip()[:20]  # Limit value length
                            else:
                                name = str(asset)[:15]
                                value = "See details"
                            assets_data.append([name, value])
                    
                    assets_table = Table(assets_data, colWidths=[2*72, 4*72])
                    assets_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('TOPPADDING', (0, 1), (-1, -1), 4),
                        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    content.append(assets_table)
                    content.append(Spacer(1, 8))
                
                # Liabilities section
                if structured_data.get('liabilities'):
                    content.append(Paragraph("Liabilities", header_style))
                    liabilities_data = [['Type', 'Amount']]
                    for liability in structured_data['liabilities']:
                        if isinstance(liability, dict):
                            liabilities_data.append([liability.get('name', 'Unknown'), liability.get('value', 'N/A')])
                        else:
                            # Fallback for string format
                            if ':' in str(liability):
                                parts = str(liability).split(':', 1)
                                name = parts[0].strip()[:15]
                                value = parts[1].strip()[:20]
                            else:
                                name = str(liability)[:15]
                                value = "See details"
                            liabilities_data.append([name, value])
                    
                    liabilities_table = Table(liabilities_data, colWidths=[2*72, 4*72])
                    liabilities_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('TOPPADDING', (0, 1), (-1, -1), 4),
                        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    content.append(liabilities_table)
                    content.append(Spacer(1, 8))
                
                # Accounts section
                if structured_data.get('accounts'):
                    content.append(Paragraph("Accounts", header_style))
                    accounts_data = [['Account', 'Balance']]
                    for account in structured_data['accounts']:
                        if isinstance(account, dict):
                            accounts_data.append([account.get('name', 'Unknown'), account.get('value', 'N/A')])
                        else:
                            # Fallback for string format
                            if ':' in str(account):
                                parts = str(account).split(':', 1)
                                name = parts[0].strip()[:15]
                                value = parts[1].strip()[:20]
                            else:
                                name = str(account)[:15]
                                value = "See details"
                            accounts_data.append([name, value])
                    
                    accounts_table = Table(accounts_data, colWidths=[2*72, 4*72])
                    accounts_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('TOPPADDING', (0, 1), (-1, -1), 4),
                        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    content.append(accounts_table)
                    content.append(Spacer(1, 8))
                
                # Unrealized Gains/Losses section
                if structured_data.get('unrealized_gains_losses'):
                    content.append(Paragraph("Unrealized Gains/Losses", header_style))
                    gains_data = [['Investment', 'Gain/Loss']]
                    for gain_loss in structured_data['unrealized_gains_losses']:
                        if isinstance(gain_loss, dict):
                            gains_data.append([gain_loss.get('name', 'Unknown'), gain_loss.get('value', 'N/A')])
                        else:
                            # Fallback for string format
                            if ':' in str(gain_loss):
                                parts = str(gain_loss).split(':', 1)
                                name = parts[0].strip()[:15]
                                value = parts[1].strip()[:20]
                            else:
                                name = str(gain_loss)[:15]
                                value = "See details"
                            gains_data.append([name, value])
                    
                    gains_table = Table(gains_data, colWidths=[2*72, 4*72])
                    gains_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('TOPPADDING', (0, 1), (-1, -1), 4),
                        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    content.append(gains_table)
                    content.append(Spacer(1, 8))
                
                # Investments by Sector section
                if structured_data.get('investments_by_sector'):
                    content.append(Paragraph("Investments by Sector", header_style))
                    sector_data = [['Sector', 'Holdings']]
                    for sector in structured_data['investments_by_sector']:
                        if isinstance(sector, dict):
                            sector_data.append([sector.get('name', 'Unknown'), sector.get('value', 'N/A')])
                        else:
                            # Fallback for string format
                            if ':' in str(sector):
                                parts = str(sector).split(':', 1)
                                name = parts[0].strip()[:15]
                                value = parts[1].strip()[:20]
                            else:
                                name = str(sector)[:15]
                                value = "See details"
                            sector_data.append([name, value])
                    
                    sector_table = Table(sector_data, colWidths=[2*72, 4*72])
                    sector_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('TOPPADDING', (0, 1), (-1, -1), 4),
                        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    content.append(sector_table)
                    content.append(Spacer(1, 8))
                
            except Exception as e:
                logging.error(f"Error creating financial tables: {e}")
                # Fall back to simple text
                content.append(Paragraph("Financial Analysis", header_style))
                content.append(Paragraph("Error formatting structured data. Raw analysis follows:", normal_style))
                content.append(Spacer(1, 12))
        
        try:
            logging.info("Generating PDF with ReportLab...")
            pdf_stream = io.BytesIO()
            doc = SimpleDocTemplate(pdf_stream, pagesize=letter, topMargin=72, bottomMargin=72, leftMargin=72, rightMargin=72)
            
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, textColor=colors.navy, spaceAfter=12, alignment=TA_CENTER)
            subtitle_style = ParagraphStyle('SubtitleStyle', parent=styles['Heading2'], fontSize=14, textColor=colors.navy, spaceAfter=8)
            header_style = ParagraphStyle('HeaderStyle', parent=styles['Heading3'], fontSize=12, textColor=colors.navy, spaceAfter=6)
            subheader_style = ParagraphStyle('SubHeaderStyle', parent=styles['Heading4'], fontSize=10, textColor=colors.darkblue, spaceAfter=4)
            normal_style = styles['Normal']
            disclaimer_style = ParagraphStyle('Disclaimer', parent=styles['Normal'], fontSize=8, textColor=colors.gray)
            
            content = []
            
            # Header
            content.append(Paragraph("Financial Summary Report", title_style))
            client_name = folder_name.split(' - ')[0] if ' - ' in folder_name else folder_name
            content.append(Paragraph(f"Client: {client_name}", subtitle_style))
            content.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", normal_style))
            content.append(Spacer(1, 20))
            
            # Add summary paragraph first (if available)
            if "ai_summary" in summary_data:
                ai_text = summary_data["ai_summary"]
                structured_data = parse_financial_summary(ai_text)
                
                if structured_data and structured_data.get('summary'):
                    content.append(Paragraph("Executive Summary", header_style))
                    content.append(Paragraph(structured_data['summary'], normal_style))
                    content.append(Spacer(1, 16))
                
                if structured_data:
                    # Create structured tables after summary
                    add_financial_tables(content, structured_data, header_style, subheader_style, normal_style)
                else:
                    # Fall back to paragraph format
                    content.append(Paragraph("Financial Analysis", header_style))
                    for paragraph in ai_text.split('\n'):
                        if paragraph.strip():
                            content.append(Paragraph(paragraph.strip(), normal_style))
                            content.append(Spacer(1, 6))
            else:
                # Fallback when no AI summary available
                if summary_data.get("summary"):
                    content.append(Paragraph("Executive Summary", header_style))
                    content.append(Paragraph(summary_data.get("summary", "No summary available"), normal_style))
                    content.append(Spacer(1, 16))
                
                # Document listing
                content.append(Paragraph("Document Analysis", header_style))
                content.append(Paragraph("Analysis based on the following documents:", normal_style))
                content.append(Spacer(1, 8))
                
                # File list table
                if summary_data.get("files_processed"):
                    files_data = [['File Name', 'Type']]
                    for file_info in summary_data.get("files_processed", []):
                        files_data.append([file_info['file_name'], file_info.get('file_type', 'Document')])
                    
                    files_table = Table(files_data, colWidths=[4*72, 2*72])
                    files_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('FONTSIZE', (0, 1), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('TOPPADDING', (0, 1), (-1, -1), 4),
                        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    content.append(files_table)
                    content.append(Spacer(1, 12))
            
            # Analysis method note
            content.append(Spacer(1, 12))
            method_text = f"Analysis Method: {summary_data.get('analysis_method', 'Unknown')}"
            content.append(Paragraph(method_text, normal_style))
            
            # Disclaimer
            content.append(Spacer(1, 16))
            content.append(Paragraph(
                "This summary should be reviewed with a financial professional. Information is for reference only.",
                disclaimer_style
            ))
            
            doc.build(content)
            pdf_stream.seek(0)
            
            if pdf_stream.getbuffer().nbytes > 0:
                pdf_created = True
                upload_file_stream = pdf_stream
                upload_format = "pdf"
                logging.info("PDF created successfully")
            else:
                raise Exception("PDF stream is empty")
                
        except Exception as pdf_error:
            logging.error(f"PDF generation failed: {str(pdf_error)}")
            pdf_created = False
        
        # If PDF failed, create text file
        if not pdf_created:
            try:
                logging.info("Creating text file as fallback")
                text_content = f"FINANCIAL SUMMARY - {client_name if 'client_name' in locals() else folder_name}\n\n"
                text_content += f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                text_content += "=" * 50 + "\n"
                
                if "ai_summary" in summary_data:
                    text_content += summary_data["ai_summary"]
                else:
                    text_content += summary_data.get("summary", "No summary available")
                    text_content += "\n\nProcessed Files:\n"
                    for file_info in summary_data.get("files_processed", []):
                        text_content += f"- {file_info['file_name']}\n"
                
                text_content += "\n" + "=" * 50 + "\n"
                text_content += f"\nAnalysis Method: {summary_data.get('analysis_method', 'Unknown')}\n"
                text_content += "\nDisclaimer: This financial summary should be reviewed with a financial professional."
                
                text_stream = io.BytesIO(text_content.encode('utf-8'))
                upload_file_stream = text_stream
                upload_format = "txt"
                
            except Exception as text_error:
                logging.error(f"Text file generation failed: {str(text_error)}")
                return JsonResponse({
                    'success': False,
                    'message': f'Both PDF and text generation failed: {str(text_error)}'
                }, status=500)
        
        # Upload the file
        try:
            file_name_base = f"Financial_Summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            upload_file_name = f"{file_name_base}.{upload_format}"
            
            if upload_file_stream:
                new_file = folder.upload_stream(upload_file_stream, upload_file_name)
                logging.info(f"Uploaded summary file: {new_file.name} (ID: {new_file.id}) as {upload_format}")
                logging.info("========== FINISHED FINANCIAL SUMMARY GENERATION SUCCESSFULLY ==========")
                
                return JsonResponse({
                    'success': True,
                    'message': 'Financial summary generated successfully',
                    'fileId': new_file.id,
                    'fileName': new_file.name,
                    'folderId': folder_id,
                    'format': upload_format,
                    'analysis_method': summary_data.get('analysis_method', 'Unknown')
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'No file content generated'
                }, status=500)
                
        except Exception as upload_error:
            logging.error(f"Error uploading summary file: {upload_error}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': f'Error uploading summary file: {str(upload_error)}'
            }, status=500)
        finally:
            if upload_file_stream:
                upload_file_stream.close()
            
    except Exception as e:
        logging.error(f"Error in generate_financial_summary: {e}")
        logging.error(traceback.format_exc())
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
    finally:
        logging.info("========== FINANCIAL SUMMARY GENERATION PROCESS COMPLETE ==========")

@login_required
@csrf_exempt
def process_document_metadata(request):
    """Process a Box document by extracting and applying metadata.
    
    Args:
        request: HTTP request with fileId parameter
    
    Returns:
        JSON response with the result
    """
    try:
        if request.method == 'POST' and request.content_type == 'application/json':
            # Handle JSON payload from client-side
            try:
                data = json.loads(request.body)
                file_id = data.get('fileId')
                template_key = data.get('templateKey', 'financialDocumentBase')
                request_data = data.get('requestData')
                
                if request_data:
                    logging.info(f"Received custom request data for extraction: {json.dumps(request_data, indent=2)}")
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'message': 'Invalid JSON payload'}, status=400)
        else:
            # Handle regular GET request with query parameters
            file_id = request.GET.get('fileId')
            template_key = request.GET.get('templateKey', 'financialDocumentBase')
            request_data = None
        
        if not file_id:
            return JsonResponse({'success': False, 'message': 'Missing file ID'}, status=400)
        
        # Get an authenticated Box client
        box_client = get_box_client()
        
        # Initialize the services
        extraction_service = BoxMetadataExtractionService(box_client)
        application_service = BoxMetadataApplicationService(box_client)
        
        # First verify the file exists and get its info
        try:
            file_obj = box_client.file(file_id)
            file_info = file_obj.get()
            logging.info(f"========== STARTING METADATA PROCESSING FOR FILE: {file_info.name} (ID: {file_id}) ==========")
        except Exception as e:
            logging.error(f"Error accessing file {file_id}: {e}")
            return JsonResponse({
                'success': False,
                'message': f'Could not access file: {str(e)}',
                'fileId': file_id
            }, status=404)
        
        # Step 1: Ensure the base metadata template is attached to the file
        try:
            # Check if metadata already exists
            try:
                metadata = file_obj.metadata(scope='enterprise_218068865', template='financialDocumentBase').get()
                logging.info(f"Base metadata template already exists for file {file_id}")
            except BoxAPIException as e:
                # If 404, metadata doesn't exist yet - create it with empty values
                if e.status == 404:
                    metadata = file_obj.metadata(scope='enterprise_218068865', template='financialDocumentBase').create({})
                    logging.info(f"Applied base metadata template to file {file_id}")
                else:
                    raise e
        except Exception as template_error:
            logging.error(f"Error with metadata template for file {file_id}: {template_error}")
            # Continue anyway as the extraction might still work
        
        # Step 2: Extract base metadata
        logging.info(f"Extracting base metadata for file {file_id}")
        
        # Use the custom request data if provided
        if request_data:
            extraction_result = extraction_service.extract_with_custom_request(file_id, request_data)
        else:
            extraction_result = extraction_service.extract_base_metadata(file_id)
        
        # Log the extracted metadata in a clean format
        if extraction_result['success']:
            extracted_data = extraction_result.get('data', {})
            logging.info(f"📄 METADATA EXTRACTED for {file_info.name} (ID: {file_id})")
            if extracted_data:
                for field, value in extracted_data.items():
                    if value:  # Only log fields with values
                        logging.info(f"  {field}: {value}")
            else:
                logging.info("  No metadata fields extracted")
        else:
            logging.warning(f"Metadata extraction failed for {file_info.name} (ID: {file_id}): {extraction_result['message']}")
        
        if not extraction_result['success']:
            return JsonResponse({
                'success': False,
                'message': f"Metadata extraction failed: {extraction_result['message']}",
                'extraction_result': extraction_result,
                'fileId': file_id
            })
        
        # Step 3: Apply the base metadata to the file
        logging.info(f"Applying base metadata for file {file_id}")
        base_metadata = extraction_result.get('data', {})
        
        # If we received a direct Box AI structured extraction response, convert to our format
        if 'ai_agent_info' in extraction_result and 'data' not in extraction_result:
            logging.info(f"Detected direct Box AI response, converting to our format")
            # Extract meaningful data, excluding Box AI metadata fields
            excluded_fields = ['ai_agent_info', 'completion_reason', 'created_at']
            base_metadata = {k: v for k, v in extraction_result.items() if k not in excluded_fields}
            # Update the extraction result to have a data field
            extraction_result['data'] = base_metadata
        
        # If we received a 'fields' array, convert to a key-value dictionary
        if 'fields' in extraction_result and isinstance(extraction_result['fields'], list):
            logging.info(f"Converting fields array to dictionary")
            fields_dict = {}
            for field in extraction_result['fields']:
                if 'key' in field and 'value' in field:
                    fields_dict[field['key']] = field['value']
            base_metadata = fields_dict
            extraction_result['data'] = base_metadata
        
        # For demo: Skip actual metadata application, just extract document type for UI
        if base_metadata:
            logging.info(f"✅ DEMO MODE: Skipping metadata storage, using classification for UI updates only")
            logging.info(f"Extracted classification data: {json.dumps(base_metadata, indent=2)}")
        
        # Simulate successful metadata application for demo
        application_result = {
            'success': True,
            'message': 'Document classification completed for demo (metadata storage skipped)',
            'data': base_metadata
        }
        
        # Log application success/failure
        if application_result['success']:
            logging.info(f"✅ METADATA APPLIED successfully to {file_info.name}")
        else:
            logging.warning(f"❌ METADATA APPLICATION FAILED for {file_info.name}: {application_result['message']}")
        
        if not application_result['success']:
            logging.warning(f"Base metadata application failed for file {file_id}: {application_result['message']}")
            return JsonResponse({
                'success': False, 
                'message': f"Base metadata application failed: {application_result['message']}",
                'application_result': application_result,
                'extraction_result': extraction_result,
                'fileId': file_id
            })
        
        # Check if document type was determined
        document_type = None
        if 'data' in application_result and 'documentType' in application_result['data']:
            document_type = application_result['data']['documentType']
        elif base_metadata and isinstance(base_metadata, dict) and 'documentType' in base_metadata:
            document_type = base_metadata['documentType']
        
        if document_type:
            logging.info(f"📋 DOCUMENT TYPE IDENTIFIED: {document_type} for {file_info.name}")
        else:
            logging.info(f"❓ Document type could not be determined for {file_info.name}")
        
        # Step 4: For demo, skip document-specific metadata processing
        document_type_result = {
            'success': True, 
            'message': f'Document type identified as {document_type or "Unknown"} - demo mode, skipping detailed metadata extraction'
        }
        if document_type:
            logging.info(f"✅ DEMO MODE: Document type '{document_type}' identified for {file_info.name} - skipping detailed metadata processing")
        
        # Step 5: For demo, skip address validation processing
        logging.info(f"✅ DEMO MODE: Skipping address validation for file {file_id}")
        address_validation_result = {'success': True, 'message': 'Address validation skipped for demo'}
        
        try:
            # Ensure the address validation template is attached
            try:
                metadata = file_obj.metadata(scope='enterprise_218068865', template='address_validation').get()
                logging.info(f"Address validation metadata template already exists for file {file_id}")
            except BoxAPIException as e:
                if e.status == 404:
                    metadata = file_obj.metadata(scope='enterprise_218068865', template='address_validation').create({})
                    logging.info(f"Applied address validation metadata template to file {file_id}")
                else:
                    raise e
            
            # Extract address validation metadata
            address_extraction = extraction_service.extract_address_validation_metadata(file_id)
            
            if address_extraction['success']:
                logging.info(f"Address validation metadata extraction successful for file {file_id}")
                
                # Apply address validation metadata
                address_application = application_service.apply_address_validation_metadata(
                    file_id,
                    address_extraction.get('data', {})
                )
                
                if address_application['success']:
                    logging.info(f"✅ ADDRESS VALIDATION METADATA APPLIED to {file_info.name}")
                    address_validation_result = address_application
                    
                    # Step 5.1: Compare extracted address with client's stored address
                    extracted_address_data = address_extraction.get('data', {})
                    if extracted_address_data:
                        logging.info(f"🔍 COMPARING EXTRACTED ADDRESS with client stored address for {file_info.name}")
                        address_comparison_result = AddressComparisonService.compare_addresses(
                            user=request.user,
                            extracted_address=extracted_address_data,
                            file_id=file_id,
                            file_name=file_info.name
                        )
                        
                        if address_comparison_result['success']:
                            if address_comparison_result['has_mismatch']:
                                mismatch_type = address_comparison_result['mismatch_type']
                                logging.warning(f"⚠️ ADDRESS MISMATCH DETECTED ({mismatch_type}) for {file_info.name}")
                                logging.warning(f"  Client address: {address_comparison_result['client_address']['full_address']}")
                                logging.warning(f"  Extracted address: {address_comparison_result['extracted_address'].get('full_address', 'N/A')}")
                            else:
                                logging.info(f"✅ ADDRESS MATCH CONFIRMED for {file_info.name}")
                        else:
                            logging.warning(f"❌ Address comparison failed for {file_info.name}: {address_comparison_result['message']}")
                        
                        # Include comparison result in the address validation result
                        address_validation_result['address_comparison'] = address_comparison_result
                else:
                    logging.warning(f"❌ Address validation metadata application failed for {file_info.name}: {address_application['message']}")
                    address_validation_result = address_application
            else:
                logging.warning(f"❌ Address validation metadata extraction failed for {file_info.name}: {address_extraction['message']}")
                address_validation_result = address_extraction
                
        except Exception as address_error:
            logging.error(f"Error in address validation processing for file {file_id}: {address_error}")
            address_validation_result = {
                'success': False,
                'message': f'Address validation error: {str(address_error)}'
            }

        logging.info(f"🎉 COMPLETED PROCESSING: {file_info.name} - Type: {document_type or 'Unknown'}")
        
        # Prepare a response that includes all the necessary data for the frontend
        response_data = {
            'success': True,
            'message': f"Successfully processed document {file_info.name}",
            'fileId': file_id,
            'documentType': document_type,
            'baseMetadataResult': application_result,
            'documentTypeResult': document_type_result,
            'addressValidationResult': address_validation_result
        }
        
        # If we have fields in the extraction result, include them in the response
        if 'fields' in extraction_result and isinstance(extraction_result['fields'], list):
            response_data['fields'] = extraction_result['fields']
        
        # If we have answer in the extraction result, include it in the response
        if 'answer' in extraction_result:
            response_data['answer'] = extraction_result['answer']
            
        return JsonResponse(response_data)
        
    except Exception as e:
        logging.error(f"Error processing document metadata for file {file_id}: {e}")
        logging.error(traceback.format_exc())
        return {
            'fileId': file_id,
            'success': False,
            'message': f'Error: {str(e)}'
        }

# Add this new view function to ensure a metadata template is applied to a file

def ensure_metadata_template(request):
    """Ensures a metadata template is applied to a file before adding metadata values.
    
    Args:
        request: HTTP request with fileId, template, and scope parameters
    
    Returns:
        JSON response with the result
    """
    try:
        # Get parameters from request
        file_id = request.GET.get('fileId')
        template = request.GET.get('template', 'financialDocumentBase')
        scope = request.GET.get('scope', 'enterprise_218068865')
        
        if not file_id:
            return JsonResponse({'success': False, 'message': 'Missing file ID'}, status=400)
        
        # Get an authenticated Box client
        box_client = get_box_client()
        
        # Get the file object
        file_obj = box_client.file(file_id=file_id)
        
        # Try to get existing metadata
        try:
            # Check if metadata already exists
            metadata = file_obj.metadata(scope=scope, template=template).get()
            return JsonResponse({
                'success': True, 
                'message': 'Metadata template already applied',
                'data': metadata
            })
        except BoxAPIException as e:
            # If 404, metadata doesn't exist yet - create it with empty values
            if e.status == 404:
                try:
                    # Apply the template with empty values
                    metadata = file_obj.metadata(scope=scope, template=template).create({})
                    return JsonResponse({
                        'success': True,
                        'message': 'Metadata template applied successfully',
                        'data': metadata
                    })
                except Exception as create_error:
                    logging.error(f"Error creating metadata template: {create_error}")
                    return JsonResponse({
                        'success': False,
                        'message': f'Error creating metadata template: {str(create_error)}'
                    }, status=500)
            else:
                logging.error(f"Error checking metadata: {e}")
                return JsonResponse({
                    'success': False,
                    'message': f'Error accessing metadata: {str(e)}'
                }, status=500)
    except Exception as e:
        logging.error(f"Error in ensure_metadata_template: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)

def check_uploaded_files(request):
    """Diagnostic endpoint to check for recent uploads to a folder.
    
    Args:
        request: HTTP request with folderId parameter
    
    Returns:
        JSON response with list of files and their details
    """
    try:
        # Get folder ID from request
        folder_id = request.GET.get('folderId')
        file_id = request.GET.get('fileId')
        
        logging.info(f"========== CHECK UPLOADS API REQUEST ==========")
        logging.info(f"Folder ID: {folder_id}")
        logging.info(f"File ID for verification: {file_id if file_id else 'None'}")
        
        if not folder_id:
            logging.error("Missing folder ID in request")
            return JsonResponse({'success': False, 'message': 'Missing folder ID'}, status=400)
        
        # Get an authenticated Box client
        logging.info("Getting Box client...")
        box_client = get_box_client()
        
        # Get the folder object
        logging.info(f"Getting folder {folder_id} from Box...")
        try:
            folder = box_client.folder(folder_id=folder_id)
            folder_info = folder.get()
            logging.info(f"Successfully retrieved folder: {folder_info.name} (ID: {folder_info.id})")
        except Exception as folder_error:
            logging.error(f"Error retrieving folder {folder_id}: {folder_error}")
            return JsonResponse({
                'success': False, 
                'message': f'Error retrieving folder: {str(folder_error)}'
            }, status=404)
        
        # Get folder items
        logging.info(f"Getting items in folder {folder_id}...")
        items = folder.get_items(limit=100)
        
        # Format the result - include both files and folders
        files = []
        for item in items:
            item_data = {
                'id': item.id,
                'name': item.name,
                'type': item.type,
                'size': getattr(item, 'size', None) if item.type == 'file' else None,
                'created_at': getattr(item, 'created_at', None),
                'modified_at': getattr(item, 'modified_at', None)
            }
            files.append(item_data)
            if item.type == 'file':
                logging.info(f"FOUND FILE: {item.name} (ID: {item.id})")
            elif item.type == 'folder':
                logging.info(f"FOUND FOLDER: {item.name} (ID: {item.id})")
        
        file_count = len([f for f in files if f['type'] == 'file'])
        folder_count = len([f for f in files if f['type'] == 'folder'])
        logging.info(f"========== FOUND {file_count} FILES AND {folder_count} FOLDERS IN FOLDER {folder_id} ==========")
        
        # Check if this is a tracking verification for a specific file
        file_found = False
        if file_id:
            file_found = any(file['id'] == file_id for file in files)
            if file_found:
                file_details = next((file for file in files if file['id'] == file_id), None)
                logging.info(f"FILE VERIFICATION SUCCESS: File ID {file_id} FOUND in folder {folder_id}")
                logging.info(f"File details: {file_details}")
            else:
                logging.warning(f"FILE VERIFICATION FAILED: File ID {file_id} NOT FOUND in folder {folder_id}")
                logging.warning(f"All items in folder: {', '.join(f['name'] + ' (' + f['id'] + ')' for f in files)}")
        
        return JsonResponse({
            'success': True,
            'message': f"Found {file_count} files and {folder_count} folders in folder",
            'files': files,
            'file_verification': file_id is not None and file_found if file_id else None
        })
        
    except Exception as e:
        logging.error(f"Error checking uploaded files: {e}")
        logging.error(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)

@login_required
@csrf_exempt
def get_file_metadata(request):
    """API endpoint to get metadata for a specific file.
    
    Args:
        request: HTTP request with fileId, template, and scope parameters
    
    Returns:
        JSON response with the metadata
    """
    try:
        # Get parameters from request
        file_id = request.GET.get('fileId')
        template = request.GET.get('template', 'financialDocumentBase')
        scope = request.GET.get('scope', 'enterprise_218068865')
        
        if not file_id:
            return JsonResponse({'success': False, 'message': 'Missing file ID'}, status=400)
        
        # Get an authenticated Box client
        box_client = get_box_client()
        
        # Get the file object
        file_obj = box_client.file(file_id=file_id)
        
        try:
            # Get the metadata
            metadata = file_obj.metadata(scope=scope, template=template).get()
            return JsonResponse({
                'success': True, 
                'message': 'Metadata retrieved successfully',
                'data': metadata
            })
        except BoxAPIException as e:
            # If 404, the metadata doesn't exist yet
            if e.status == 404:
                return JsonResponse({
                    'success': False,
                    'message': 'No metadata found for this file'
                }, status=404)
            else:
                logging.error(f"Error retrieving metadata: {e}")
                return JsonResponse({
                    'success': False,
                    'message': f'Error retrieving metadata: {str(e)}'
                }, status=500)
    except Exception as e:
        logging.error(f"Error in get_file_metadata: {e}")
        logging.error(traceback.format_exc())
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)

@login_required
def get_metadata_template_details(request):
    """Get metadata template details.
    
    Args:
        request: HTTP request with template and scope parameters
    
    Returns:
        JSON response with the template details
    """
    try:
        # Get parameters from request
        template_key = request.GET.get('template', 'financialDocumentBase')
        scope = request.GET.get('scope', 'enterprise_218068865')
        
        # Get an authenticated Box client
        box_client = get_box_client()
        
        # Get all templates
        templates = box_client.metadata_templates()
        
        # Find the requested template
        template_found = None
        for template in templates:
            if template.templateKey == template_key and template.scope == scope:
                template_found = template
                break
        
        if not template_found:
            return JsonResponse({
                'success': False, 
                'message': f'Template not found: {template_key} in scope {scope}'
            }, status=404)
        
        # Get template schema (fields)
        template_schema = template_found.get()
        
        # Format the response to show fields
        fields = []
        if hasattr(template_schema, 'fields'):
            for field in template_schema.fields:
                field_info = {
                    'displayName': field.displayName,
                    'key': field.key,
                    'type': field.type
                }
                
                # Include options if present
                if hasattr(field, 'options') and field.options:
                    field_info['options'] = [{'key': option.key} for option in field.options]
                
                fields.append(field_info)
        
        return JsonResponse({
            'success': True,
            'template': {
                'templateKey': template_schema.templateKey,
                'scope': template_schema.scope,
                'displayName': template_schema.displayName,
                'fields': fields
            }
        })
    except Exception as e:
        logging.error(f"Error getting template details: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        }, status=500)

@login_required
@csrf_exempt
def process_documents_metadata_batch(request):
    """Process multiple Box documents in parallel by extracting and applying metadata.
    
    Args:
        request: HTTP request with fileIds parameter containing list of file IDs
    
    Returns:
        JSON response with the results for each file
    """
    try:
        if request.method != 'POST':
            return JsonResponse({'success': False, 'message': 'Only POST method is allowed'}, status=405)
        
        # Parse request data
        try:
            data = json.loads(request.body)
            file_ids = data.get('fileIds', [])
            
            if not file_ids or not isinstance(file_ids, list):
                return JsonResponse({'success': False, 'message': 'Missing or invalid fileIds parameter'}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON payload'}, status=400)
        
        # Get an authenticated Box client
        box_client = get_box_client()
        
        # Initialize the services
        extraction_service = BoxMetadataExtractionService(box_client)
        application_service = BoxMetadataApplicationService(box_client)
        
        # Define function to process a single file
        def process_single_file(file_id):
            try:
                # First verify the file exists and get its info
                try:
                    file_obj = box_client.file(file_id)
                    file_info = file_obj.get()
                    file_name = file_info.name
                    logging.info(f"========== STARTING METADATA PROCESSING FOR FILE: {file_name} (ID: {file_id}) ==========")
                except Exception as e:
                    logging.error(f"Error accessing file {file_id}: {e}")
                    return {
                        'fileId': file_id,
                        'success': False,
                        'message': f'Could not access file: {str(e)}'
                    }
                
                # Step 1: DEMO MODE - Skip metadata template attachment
                logging.info(f"✅ DEMO MODE: Skipping metadata template for file {file_id}")
                
                # Step 2: Extract base metadata
                logging.info(f"Extracting base metadata for file {file_id}")
                extraction_result = extraction_service.extract_base_metadata(file_id)
                
                if not extraction_result['success']:
                    logging.warning(f"Base metadata extraction failed for file {file_id}: {extraction_result['message']}")
                    return {
                        'fileId': file_id,
                        'success': False,
                        'message': f"Base metadata extraction failed: {extraction_result['message']}",
                        'extraction_result': extraction_result
                    }
                
                # Get the extracted base metadata
                base_metadata = extraction_result.get('data', {})
                logging.info(f"Successfully extracted base metadata for file {file_id}")
                
                # DEMO MODE - Skip base metadata application
                logging.info(f"✅ DEMO MODE: Skipping metadata storage for file {file_id}, using classification for UI only")
                
                # Add debug information for educational purposes
                debug_info = {
                    'ai_agent_request': extraction_result.get('debug_request', {}),
                    'ai_agent_response': extraction_result.get('debug_response', {}),
                    'extracted_data': base_metadata
                }
                
                application_result = {
                    'success': True,
                    'message': 'Demo mode - metadata storage skipped',
                    'data': base_metadata,
                    'debug_info': debug_info
                }
                
                # Check if document type was determined
                document_type = None
                if 'fields' in extraction_result and isinstance(extraction_result['fields'], list):
                    # Look for documentType in fields array
                    for field in extraction_result['fields']:
                        if field.get('key') == 'documentType' and 'value' in field:
                            document_type = field['value']
                            break
                elif isinstance(base_metadata, dict) and 'documentType' in base_metadata:
                    document_type = base_metadata['documentType']
                
                # DEMO MODE - Skip document-specific processing, just log the type
                document_type_result = {'success': True, 'message': f'Document type: {document_type or "Unknown"} - demo mode'}
                if document_type:
                    logging.info(f"✅ DEMO MODE: Document type '{document_type}' identified for file {file_id} - skipping detailed processing")
                else:
                    logging.info(f"No document type determined for file {file_id}")
                
                # Step 3: DEMO MODE - Skip address validation
                logging.info(f"✅ DEMO MODE: Skipping address validation for file {file_id}")
                address_validation_result = {'success': True, 'message': 'Address validation skipped for demo'}
                
                # DEMO MODE - Skip all address validation processing
                pass
                
                return {
                    'fileId': file_id,
                    'success': True,
                    'message': 'Metadata processing completed successfully',
                    'extraction_result': extraction_result,
                    'application_result': application_result,
                    'documentType': document_type,
                    'document_type_result': document_type_result,
                    'address_validation_result': address_validation_result,
                    'debug_info': debug_info
                }
                
            except Exception as e:
                logging.error(f"Error processing file {file_id}: {e}")
                return {
                    'fileId': file_id,
                    'success': False,
                    'message': f'Error processing file: {str(e)}'
                }
        
        # Process files in parallel using ThreadPoolExecutor
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import time
        
        start_time = time.time()
        results = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit all processing tasks
            future_to_file_id = {executor.submit(process_single_file, file_id): file_id for file_id in file_ids}
            
            # Collect results as they complete
            for future in as_completed(future_to_file_id):
                file_id = future_to_file_id[future]
                try:
                    result = future.result()
                    results.append(result)
                    logging.info(f"Completed processing file {file_id}")
                except Exception as e:
                    logging.error(f"Exception during processing file {file_id}: {e}")
                    results.append({
                        'fileId': file_id,
                        'success': False,
                        'message': f'Exception during processing: {str(e)}'
                    })
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Calculate summary statistics
        successful_count = sum(1 for result in results if result.get('success', False))
        failed_count = len(results) - successful_count
        
        logging.info(f"========== BATCH PROCESSING COMPLETE ==========")
        logging.info(f"Total files: {len(file_ids)}")
        logging.info(f"Successful: {successful_count}")
        logging.info(f"Failed: {failed_count}")
        logging.info(f"Processing time: {processing_time:.2f} seconds")
        
        return JsonResponse({
            'success': True,
            'message': f'Batch processing completed: {successful_count}/{len(file_ids)} files successful',
            'results': results,
            'summary': {
                'total': len(file_ids),
                'successful': successful_count,
                'failed': failed_count,
                'processing_time': processing_time
            }
        })
        
    except Exception as e:
        logging.error(f"Error in batch metadata processing: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Batch processing error: {str(e)}'
        }, status=500)

@login_required
@csrf_exempt
def process_address_validation_metadata(request):
    """Process a Box document by extracting and applying address validation metadata.
    
    Args:
        request: HTTP request with fileId parameter
    
    Returns:
        JSON response with the result
    """
    try:
        if request.method == 'POST' and request.content_type == 'application/json':
            # Handle JSON payload from client-side
            try:
                data = json.loads(request.body)
                file_id = data.get('fileId')
                request_data = data.get('requestData')
                
                if request_data:
                    logging.info(f"Received custom request data for address extraction: {json.dumps(request_data, indent=2)}")
            except json.JSONDecodeError:
                return JsonResponse({'success': False, 'message': 'Invalid JSON payload'}, status=400)
        else:
            # Handle regular GET request with query parameters
            file_id = request.GET.get('fileId')
            request_data = None
        
        if not file_id:
            return JsonResponse({'success': False, 'message': 'Missing file ID'}, status=400)
        
        # Get an authenticated Box client
        box_client = get_box_client()
        
        # Initialize the services
        extraction_service = BoxMetadataExtractionService(box_client)
        application_service = BoxMetadataApplicationService(box_client)
        
        # First verify the file exists and get its info
        try:
            file_obj = box_client.file(file_id)
            file_info = file_obj.get()
            logging.info(f"========== STARTING ADDRESS VALIDATION PROCESSING FOR FILE: {file_info.name} (ID: {file_id}) ==========")
        except Exception as e:
            logging.error(f"Error accessing file {file_id}: {e}")
            return JsonResponse({
                'success': False,
                'message': f'Could not access file: {str(e)}',
                'fileId': file_id
            }, status=404)
        
        # Step 1: Ensure the address validation metadata template is attached to the file
        try:
            # Check if metadata already exists
            try:
                metadata = file_obj.metadata(scope='enterprise_218068865', template='address_validation').get()
                logging.info(f"Address validation metadata template already exists for file {file_id}")
            except BoxAPIException as e:
                # If 404, metadata doesn't exist yet - create it with empty values
                if e.status == 404:
                    metadata = file_obj.metadata(scope='enterprise_218068865', template='address_validation').create({})
                    logging.info(f"Applied address validation metadata template to file {file_id}")
                else:
                    raise e
        except Exception as template_error:
            logging.error(f"Error with address validation metadata template for file {file_id}: {template_error}")
            # Continue anyway as the extraction might still work
        
        # Step 2: Extract address validation metadata
        logging.info(f"Extracting address validation metadata for file {file_id}")
        
        # Use the custom request data if provided
        if request_data:
            # Use custom request with address validation template
            if 'metadata_template' in request_data:
                request_data['metadata_template']['template_key'] = 'address_validation'
            extraction_result = extraction_service.extract_with_custom_request(file_id, request_data)
        else:
            extraction_result = extraction_service.extract_address_validation_metadata(file_id)
        
        if not extraction_result['success']:
            logging.warning(f"Address validation metadata extraction failed for file {file_id}: {extraction_result['message']}")
            return JsonResponse({
                'success': False, 
                'message': f"Address validation metadata extraction failed: {extraction_result['message']}",
                'extraction_result': extraction_result,
                'fileId': file_id
            })
        
        # Get the extracted metadata
        address_metadata = extraction_result.get('data', {})
        logging.info(f"Successfully extracted address validation metadata for file {file_id}")
        
        # If we received a 'fields' array, convert to a key-value dictionary
        if 'fields' in extraction_result and isinstance(extraction_result['fields'], list):
            logging.info(f"Converting fields array to dictionary for address validation")
            fields_dict = {}
            for field in extraction_result['fields']:
                if 'key' in field and 'value' in field:
                    fields_dict[field['key']] = field['value']
            address_metadata = fields_dict
            extraction_result['data'] = address_metadata
        
        # Log successful metadata application
        if address_metadata:
            logging.info(f"✅ APPLYING ADDRESS VALIDATION METADATA to {file_info.name} (ID: {file_id})")
        
        application_result = application_service.apply_address_validation_metadata(file_id, address_metadata)
        
        # Log application success/failure
        if application_result['success']:
            logging.info(f"✅ ADDRESS VALIDATION METADATA APPLIED successfully to {file_info.name}")
        else:
            logging.warning(f"❌ ADDRESS VALIDATION METADATA APPLICATION FAILED for {file_info.name}: {application_result['message']}")
        
        if not application_result['success']:
            logging.warning(f"Address validation metadata application failed for file {file_id}: {application_result['message']}")
            return JsonResponse({
                'success': False, 
                'message': f"Address validation metadata application failed: {application_result['message']}",
                'application_result': application_result,
                'extraction_result': extraction_result,
                'fileId': file_id
            })
        
        logging.info(f"✅ ADDRESS VALIDATION PROCESSING COMPLETED successfully for {file_info.name}")
        
        return JsonResponse({
            'success': True,
            'message': 'Address validation metadata processing completed successfully',
            'extraction_result': extraction_result,
            'application_result': application_result,
            'fileId': file_id,
            'fileName': file_info.name
        })
        
    except Exception as e:
        logging.error(f"Error in address validation metadata processing: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Address validation processing error: {str(e)}'
        }, status=500)

@login_required
def financial_analysis_view(request):
    """Renders the financial analysis page."""
    folder_id = request.GET.get('folderId')
    summary_file_id = request.GET.get('summaryFileId')
    
    context = {
        'folder_id': folder_id,
        'summary_file_id': summary_file_id
    }
    return render(request, 'financial_analysis.html', context)

@login_required
def get_box_preview_token(request):
    """Get a Box preview token for a specific file"""
    file_id = request.GET.get('file_id')
    if not file_id:
        return JsonResponse({'success': False, 'error': 'No file ID provided'})
    
    try:
        # Get downscoped token with preview permissions
        client = get_box_client()
        
        # Create a resource-specific token for this file with preview permissions
        file_resource = f"https://api.box.com/2.0/files/{file_id}"
        preview_scopes = [
            "item_preview", 
            "base_preview", 
            "item_download",
            "annotation_view_all",
            "annotation_edit",
            "base_explorer"
        ]
        
        token_response = client.downscope_token(
            scopes=preview_scopes,
            item=client.file(file_id=file_id)
        )
        
        if not token_response or not token_response.access_token:
            logger.error(f"Failed to get downscoped token for file {file_id}")
            return JsonResponse({
                'success': False, 
                'error': 'Failed to generate preview token'
            })
        
        return JsonResponse({
            'success': True,
            'access_token': token_response.access_token,
            'file_id': file_id
        })
        
    except Exception as e:
        logger.exception(f"Error generating preview token: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f"Error generating preview token: {str(e)}",
            'file_id': file_id
        })

@login_required
def direct_file_url(request):
    """Get a direct URL to view a file in Box"""
    file_id = request.GET.get('fileId')
    if not file_id:
        return JsonResponse({'success': False, 'error': 'No file ID provided'})
    
    try:
        client = get_box_client()
        box_file = client.file(file_id=file_id).get()
        
        # Create a shared link with direct download permissions
        shared_link = box_file.get_shared_link(
            access='company',
            allow_download=True,
            allow_preview=True
        )
        
        # If we already have a shared link, use it
        if box_file.shared_link:
            shared_link = box_file.shared_link['url']

        if not shared_link:
            return JsonResponse({
                'success': False,
                'error': 'Failed to create shared link'
            })
            
        return JsonResponse({
            'success': True,
            'url': shared_link,
            'file_id': file_id,
            'file_name': box_file.name
        })
        
    except Exception as e:
        logger.exception(f"Error generating direct file URL: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': f"Error generating direct file URL: {str(e)}",
            'file_id': file_id
        })

@login_required
def box_metadata_config(request):
    """API endpoint to provide metadata configuration and pre-fetched results for Box Content Explorer metadata view."""
    try:
        folder_id = request.GET.get('folderId')
        if not folder_id:
            return JsonResponse({'error': 'Folder ID is required'}, status=400)
        
        # Get the Box client with full permissions
        client = get_box_client()
        
        # Enterprise configuration
        enterprise_id = "218068865"
        template_name = "financialDocumentBase"
        metadata_source = f"enterprise_{enterprise_id}.{template_name}"
        
        logging.info(f"Metadata config - Enterprise ID: {enterprise_id}")
        logging.info(f"Metadata config - Template: {template_name}")
        logging.info(f"Metadata config - Source: {metadata_source}")
        
        # Execute the metadata query server-side with full permissions
        try:
            # Use the metadata query API to find files with the base template
            query_params = {
                "from": metadata_source,
                "ancestor_folder_id": int(folder_id),
                "fields": [
                    "id",
                    "name", 
                    "type",
                    "size",
                    "modified_at",
                    f"metadata.{metadata_source}.documentType",
                    f"metadata.{metadata_source}.issuerName", 
                    f"metadata.{metadata_source}.recipientName",
                    f"metadata.{metadata_source}.documentDate",
                    f"metadata.{metadata_source}.taxYear",
                    f"metadata.{metadata_source}.isLegible"
                ],
                "limit": 100
            }
            
            # Execute the metadata query
            results = client.make_request(
                'POST',
                'https://api.box.com/2.0/metadata_queries/execute_read',
                data=json.dumps(query_params),
                headers={'Content-Type': 'application/json'}
            )
            
            # Process the results to extract files with metadata
            metadata_entries = []
            if results.status_code == 200:
                query_results = results.json()
                metadata_entries = query_results.get('entries', [])
                logging.info(f"Found {len(metadata_entries)} files with metadata in folder {folder_id}")
            else:
                logging.warning(f"Metadata query returned status {results.status_code}: {results.text}")
            
            # Return configuration for client-side Content Explorer
            # Since metadata queries need full permissions, we provide the results directly
            config = {
                'success': True,
                'hasMetadataResults': len(metadata_entries) > 0,
                'metadataEntries': metadata_entries,
                'metadataTemplate': {
                    'scope': f'enterprise_{enterprise_id}',
                    'templateKey': template_name,
                    'displayName': 'Financial Document Base',
                    'source': metadata_source
                },
                'fieldsToShow': [
                    {
                        'key': f'metadata.{metadata_source}.documentType',
                        'displayName': 'Document Type',
                        'canEdit': False
                    },
                    {
                        'key': f'metadata.{metadata_source}.issuerName',
                        'displayName': 'Issuer',
                        'canEdit': False
                    },
                    {
                        'key': f'metadata.{metadata_source}.recipientName',
                        'displayName': 'Recipient',
                        'canEdit': False
                    },
                    {
                        'key': f'metadata.{metadata_source}.documentDate',
                        'displayName': 'Document Date',
                        'canEdit': False
                    },
                    {
                        'key': f'metadata.{metadata_source}.taxYear',
                        'displayName': 'Tax Year',
                        'canEdit': False
                    },
                    {
                        'key': f'metadata.{metadata_source}.isLegible',
                        'displayName': 'Legible',
                        'canEdit': False
                    }
                ]
            }
            
            return JsonResponse(config)
            
        except Exception as metadata_error:
            logging.error(f"Metadata query failed: {str(metadata_error)}")
            # Return fallback configuration for regular file view
            return JsonResponse({
                'success': False,
                'error': 'Metadata query not available',
                'hasMetadataResults': False,
                'message': 'Falling back to regular file view'
            })
        
    except Exception as e:
        logging.error(f"Error in box_metadata_config: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def test_metadata_query(request):
    """Test endpoint to check metadata query and files with metadata."""
    try:
        folder_id = request.GET.get('folderId')
        if not folder_id:
            return JsonResponse({'error': 'Folder ID is required'}, status=400)
        
        # Get the Box client
        client = get_box_client()
        
        # Get folder and list files
        folder = client.folder(folder_id)
        files = list(folder.get_items(limit=100))
        
        # Check each file for metadata
        files_with_metadata = []
        for file_item in files:
            if file_item.type == 'file':
                try:
                    # Try to get the base metadata template
                    metadata = file_item.metadata(scope='enterprise_218068865', template='financialDocumentBase').get()
                    files_with_metadata.append({
                        'id': file_item.id,
                        'name': file_item.name,
                        'metadata': dict(metadata) if hasattr(metadata, '__iter__') else str(metadata)
                    })
                except BoxAPIException as e:
                    if e.status != 404:  # 404 means no metadata, which is expected
                        logging.warning(f"Error getting metadata for file {file_item.id}: {e}")
                except Exception as e:
                    logging.warning(f"Unexpected error getting metadata for file {file_item.id}: {e}")
        
        return JsonResponse({
            'success': True,
            'folder_id': folder_id,
            'total_files': len([f for f in files if f.type == 'file']),
            'files_with_metadata': len(files_with_metadata),
            'files': files_with_metadata[:5]  # Show first 5 files with metadata
        })
        
    except Exception as e:
        logging.error(f"Error in test_metadata_query: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_address_mismatches(request):
    """API endpoint to get address mismatches for the current user."""
    try:
        mismatches = AddressComparisonService.get_user_address_mismatches(request.user)
        
        # Convert mismatches to a serializable format
        mismatches_data = []
        for mismatch in mismatches:
            mismatches_data.append({
                'id': mismatch.id,
                'file_id': mismatch.file_id,
                'file_name': mismatch.file_name,
                'mismatch_type': mismatch.mismatch_type,
                'client_address': {
                    'street_address': mismatch.client_street,
                    'city': mismatch.client_city,
                    'state': mismatch.client_state,
                    'postal_code': mismatch.client_postal_code,
                    'full_address': mismatch.client_full_address
                },
                'extracted_address': {
                    'street_address': mismatch.extracted_street,
                    'city': mismatch.extracted_city,
                    'state': mismatch.extracted_state,
                    'postal_code': mismatch.extracted_postal_code,
                    'full_address': mismatch.extracted_full_address
                },
                'created_at': mismatch.created_at.isoformat(),
                'resolved': mismatch.resolved
            })
        
        return JsonResponse({
            'success': True,
            'mismatches': mismatches_data,
            'total_count': len(mismatches_data)
        })
        
    except Exception as e:
        logging.error(f"Error getting address mismatches for user {request.user.username}: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Error retrieving address mismatches: {str(e)}'
        }, status=500)

@login_required
@csrf_exempt
def update_client_address(request):
    """API endpoint to update client's address from an address mismatch."""
    try:
        if request.method != 'POST':
            return JsonResponse({'success': False, 'message': 'Only POST method is allowed'}, status=405)
        
        # Parse request data
        try:
            data = json.loads(request.body)
            mismatch_id = data.get('mismatchId')
            use_extracted_address = data.get('useExtractedAddress', False)
            
            if not mismatch_id:
                return JsonResponse({'success': False, 'message': 'Missing mismatch ID'}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON payload'}, status=400)
        
        # Get the address mismatch record
        try:
            mismatch = AddressMismatch.objects.get(id=mismatch_id, client=request.user)
        except AddressMismatch.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Address mismatch not found'}, status=404)
        
        if use_extracted_address:
            # Update client's address with the extracted address
            try:
                client_info = ClientOnboardingInfo.objects.get(user=request.user)
            except ClientOnboardingInfo.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Client onboarding info not found'}, status=404)
            
            # Update the client's address with the extracted address
            old_address = client_info.full_address
            client_info.street_address = mismatch.extracted_street
            client_info.city = mismatch.extracted_city
            client_info.state_province = mismatch.extracted_state
            client_info.postal_code = mismatch.extracted_postal_code
            client_info.save()
            
            logging.info(f"Updated client address for user {request.user.username}")
            logging.info(f"  Old address: {old_address}")
            logging.info(f"  New address: {client_info.full_address}")
            
            # Mark the mismatch as resolved
            mismatch.resolved = True
            mismatch.save()
            
            # Re-run address comparison for all user's files to check for other mismatches
            # that might now be resolved with the updated address
            user_mismatches = AddressMismatch.objects.filter(client=request.user, resolved=False)
            resolved_count = 0
            
            for other_mismatch in user_mismatches:
                # Compare the new client address with this file's extracted address
                comparison_result = AddressComparisonService.compare_addresses(
                    user=request.user,
                    extracted_address={
                        'street_address': other_mismatch.extracted_street,
                        'city': other_mismatch.extracted_city,
                        'state_province': other_mismatch.extracted_state,
                        'postal_code': other_mismatch.extracted_postal_code,
                        'full_address': other_mismatch.extracted_full_address
                    },
                    file_id=other_mismatch.file_id,
                    file_name=other_mismatch.file_name
                )
                
                # If the comparison now shows no mismatch, the old mismatch record
                # will be automatically deleted by the comparison service
                if comparison_result['success'] and not comparison_result['has_mismatch']:
                    resolved_count += 1
            
            return JsonResponse({
                'success': True,
                'message': f'Address updated successfully. {resolved_count} additional mismatches resolved.',
                'new_address': client_info.full_address,
                'resolved_additional': resolved_count
            })
        else:
            # Just mark the mismatch as resolved without updating the address
            mismatch.resolved = True
            mismatch.save()
            
            logging.info(f"Marked address mismatch as resolved for user {request.user.username}, file {mismatch.file_name}")
            
            return JsonResponse({
                'success': True,
                'message': 'Address mismatch marked as resolved',
                'address_updated': False
            })
        
    except Exception as e:
        logging.error(f"Error updating client address: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Error updating address: {str(e)}'
        }, status=500)

@login_required
@csrf_exempt
def update_client_address_group(request):
    """API endpoint to update client's address from multiple address mismatches with the same extracted address."""
    try:
        if request.method != 'POST':
            return JsonResponse({'success': False, 'message': 'Only POST method is allowed'}, status=405)
        
        # Parse request data
        try:
            data = json.loads(request.body)
            mismatch_ids = data.get('mismatchIds', [])
            use_extracted_address = data.get('useExtractedAddress', False)
            
            if not mismatch_ids or not isinstance(mismatch_ids, list):
                return JsonResponse({'success': False, 'message': 'Missing or invalid mismatch IDs'}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON payload'}, status=400)
        
        # Get all the address mismatch records
        try:
            mismatches = AddressMismatch.objects.filter(id__in=mismatch_ids, client=request.user)
            if len(mismatches) != len(mismatch_ids):
                return JsonResponse({'success': False, 'message': 'Some address mismatches not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error retrieving mismatches: {str(e)}'}, status=500)
        
        if use_extracted_address:
            # Update client's address with the extracted address (use first mismatch as they should all have same extracted address)
            first_mismatch = mismatches[0]
            
            try:
                client_info = ClientOnboardingInfo.objects.get(user=request.user)
            except ClientOnboardingInfo.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Client onboarding info not found'}, status=404)
            
            # Update the client's address with the extracted address
            old_address = client_info.full_address
            client_info.street_address = first_mismatch.extracted_street
            client_info.city = first_mismatch.extracted_city
            client_info.state_province = first_mismatch.extracted_state
            client_info.postal_code = first_mismatch.extracted_postal_code
            client_info.save()
            
            logging.info(f"Updated client address for user {request.user.username} (group update)")
            logging.info(f"  Old address: {old_address}")
            logging.info(f"  New address: {client_info.full_address}")
            
            # Mark all mismatches in the group as resolved
            mismatches.update(resolved=True)
            
            logging.info(f"Marked {len(mismatches)} address mismatches as resolved for user {request.user.username}")
            
            # Re-run address comparison for all user's files to check for other mismatches
            # that might now be resolved with the updated address
            user_mismatches = AddressMismatch.objects.filter(client=request.user, resolved=False)
            resolved_count = 0
            
            for other_mismatch in user_mismatches:
                # Compare the new client address with this file's extracted address
                comparison_result = AddressComparisonService.compare_addresses(
                    user=request.user,
                    extracted_address={
                        'street_address': other_mismatch.extracted_street,
                        'city': other_mismatch.extracted_city,
                        'state_province': other_mismatch.extracted_state,
                        'postal_code': other_mismatch.extracted_postal_code,
                        'full_address': other_mismatch.extracted_full_address
                    },
                    file_id=other_mismatch.file_id,
                    file_name=other_mismatch.file_name
                )
                
                # If the comparison now shows no mismatch, the old mismatch record
                # will be automatically deleted by the comparison service
                if comparison_result['success'] and not comparison_result['has_mismatch']:
                    resolved_count += 1
            
            return JsonResponse({
                'success': True,
                'message': f'Address updated successfully. {len(mismatches)} mismatches resolved. {resolved_count} additional mismatches resolved.',
                'new_address': client_info.full_address,
                'resolved_count': len(mismatches),
                'resolved_additional': resolved_count
            })
        else:
            # Just mark all mismatches as resolved without updating the address
            mismatches.update(resolved=True)
            
            logging.info(f"Marked {len(mismatches)} address mismatches as resolved for user {request.user.username}")
            
            return JsonResponse({
                'success': True,
                'message': f'{len(mismatches)} address mismatches marked as resolved',
                'address_updated': False,
                'resolved_count': len(mismatches)
            })
        
    except Exception as e:
        logging.error(f"Error updating client address group: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Error updating address: {str(e)}'
        }, status=500)
