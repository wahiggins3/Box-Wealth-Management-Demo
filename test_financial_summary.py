#!/usr/bin/env python
"""
Test Financial Summary Generation

This script tests each step of the financial summary generation process
to identify where failures are occurring.
"""

import os
import django
import sys
import json
import requests
from pathlib import Path

# Setup Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portal_project.settings')
django.setup()

from core.utils import get_box_client
from django.conf import settings

def test_box_connection():
    """Test Box client connection"""
    print("=== Testing Box Connection ===")
    try:
        client = get_box_client()
        print("✅ Box client created successfully")
        
        # Test with user info
        try:
            user = client.user().get()
            print(f"✅ Authenticated as: {user.name} ({user.login})")
            return client
        except Exception as e:
            print(f"⚠️  Authentication issue: {e}")
            return client
    except Exception as e:
        print(f"❌ Failed to create Box client: {e}")
        return None

def test_folder_access(client, folder_id):
    """Test accessing a specific folder"""
    print(f"\n=== Testing Folder Access: {folder_id} ===")
    try:
        folder = client.folder(folder_id)
        folder_info = folder.get()
        print(f"✅ Folder accessed: {folder_info.name}")
        
        # List files in folder
        items = folder.get_items(limit=10)
        files = [item for item in items if item.type == 'file']
        print(f"✅ Found {len(files)} files in folder")
        
        for file_item in files[:3]:  # Show first 3 files
            print(f"   - {file_item.name} (ID: {file_item.id})")
        
        return files
    except Exception as e:
        print(f"❌ Failed to access folder: {e}")
        return []

def test_box_ai_request(client, files):
    """Test Box AI Ask API request"""
    print(f"\n=== Testing Box AI Ask API ===")
    if not files:
        print("❌ No files to test with")
        return False
        
    try:
        # Get access token
        auth = client.auth
        access_token = auth._access_token
        print("✅ Got access token")
        
        # Test with first file
        test_file = files[0]
        print(f"Testing with file: {test_file.name} (ID: {test_file.id})")
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Test payload
        ai_request_payload = {
            "mode": "single_item_qa",
            "prompt": "What type of document is this?",
            "items": [{"id": test_file.id, "type": "file"}],
            "ai_agent": {
                "id": "1329589",
                "type": "ai_agent_id"
            }
        }
        
        print("Making Box AI Ask API request...")
        response = requests.post(
            'https://api.box.com/2.0/ai/ask',
            headers=headers,
            json=ai_request_payload,
            timeout=30
        )
        
        print(f"Response status: {response.status_code}")
        
        if response.status_code in [200, 201, 202]:
            ai_response = response.json()
            answer = ai_response.get('answer', '')
            print(f"✅ Box AI responded: {answer[:100]}...")
            return True
        else:
            error_details = response.text
            try:
                error_json = response.json()
                error_details = json.dumps(error_json, indent=2)
            except:
                pass
            print(f"❌ Box AI API failed: {response.status_code}")
            print(f"Error details: {error_details}")
            return False
            
    except Exception as e:
        print(f"❌ Box AI test failed: {e}")
        return False

def test_pdf_generation():
    """Test PDF generation with ReportLab"""
    print(f"\n=== Testing PDF Generation ===")
    try:
        import io
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        
        # Create a simple test PDF
        pdf_stream = io.BytesIO()
        doc = SimpleDocTemplate(pdf_stream, pagesize=letter)
        styles = getSampleStyleSheet()
        
        content = [
            Paragraph("Test Financial Summary", styles['Title']),
            Paragraph("This is a test PDF generation.", styles['Normal'])
        ]
        
        doc.build(content)
        pdf_stream.seek(0)
        
        if pdf_stream.getbuffer().nbytes > 0:
            print("✅ PDF generation successful")
            print(f"   PDF size: {pdf_stream.getbuffer().nbytes} bytes")
            return True
        else:
            print("❌ PDF generation failed - empty stream")
            return False
            
    except Exception as e:
        print(f"❌ PDF generation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Financial Summary Generation Diagnostic")
    print("=" * 50)
    
    # Test 1: Box connection
    client = test_box_connection()
    if not client:
        print("\n❌ Cannot proceed without Box connection")
        return
    
    # Test 2: Try with a known folder ID (from the onboarding flow)
    print("\nEnter a folder ID to test with (or press Enter to skip):")
    folder_id = input().strip()
    
    if folder_id:
        files = test_folder_access(client, folder_id)
        
        # Test 3: Box AI API
        if files:
            test_box_ai_request(client, files)
    
    # Test 4: PDF generation
    test_pdf_generation()
    
    print("\n" + "=" * 50)
    print("Diagnostic complete. Check results above for issues.")

if __name__ == "__main__":
    main() 