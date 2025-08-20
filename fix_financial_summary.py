#!/usr/bin/env python
"""
Fix Financial Summary Generation

This script provides an improved version of the financial summary generation
with better error handling and fallback mechanisms.
"""

import os
import django
import sys
import json
import requests
import logging
import io
import traceback
from datetime import datetime

# Setup Django environment
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portal_project.settings')
django.setup()

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from core.utils import get_box_client
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

logger = logging.getLogger(__name__)

def create_fallback_summary(files, folder_name):
    """Create a basic fallback summary when AI fails"""
    print(f"Creating fallback summary for {len(files)} files")
    
    summary_data = {
        "summary": f"Financial document analysis for {folder_name}",
        "total_files": len(files),
        "files_processed": [],
        "generated_on": datetime.now().isoformat(),
        "note": "This is a basic summary generated when AI analysis was unavailable."
    }
    
    for file_item in files:
        file_info = {
            "file_name": file_item.name,
            "file_id": file_item.id,
            "file_type": "Document"
        }
        summary_data["files_processed"].append(file_info)
    
    return summary_data

def test_box_ai_with_fallback(client, files):
    """Test Box AI with multiple agent configurations and fallback"""
    if not files:
        return None, "No files available for analysis"
    
    # Get access token
    try:
        auth = client.auth
        access_token = auth._access_token
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    except Exception as e:
        return None, f"Failed to get access token: {str(e)}"
    
    # Try different AI agent configurations
    ai_agents = [
        {"id": "1329589", "type": "ai_agent_id"},  # Original
        {"type": "ai_agent_ask"},  # Generic ask agent
        {"type": "ai_agent_text_gen"},  # Text generation agent
    ]
    
    for i, ai_agent in enumerate(ai_agents):
        try:
            print(f"Trying AI agent {i+1}: {ai_agent}")
            
            # Use first file for testing
            test_file = files[0]
            
            ai_request_payload = {
                "mode": "single_item_qa",
                "prompt": "Provide a brief financial summary of this document, including any account balances, investment details, or financial information present.",
                "items": [{"id": test_file.id, "type": "file"}],
                "ai_agent": ai_agent
            }
            
            response = requests.post(
                'https://api.box.com/2.0/ai/ask',
                headers=headers,
                json=ai_request_payload,
                timeout=30
            )
            
            print(f"AI agent {i+1} response status: {response.status_code}")
            
            if response.status_code in [200, 201, 202]:
                ai_response = response.json()
                answer = ai_response.get('answer', '')
                if answer:
                    print(f"✅ AI agent {i+1} successful")
                    return ai_agent, answer
            else:
                error_details = response.text
                print(f"AI agent {i+1} failed: {response.status_code} - {error_details[:200]}")
                
        except Exception as e:
            print(f"AI agent {i+1} exception: {str(e)}")
            continue
    
    return None, "All AI agents failed"

def improved_generate_financial_summary(folder_id):
    """Improved financial summary generation with better error handling"""
    print(f"=== Starting Improved Financial Summary Generation ===")
    print(f"Folder ID: {folder_id}")
    
    try:
        # Get Box client
        box_client = get_box_client()
        print("✅ Box client created")
        
        # Access folder and get files
        folder = box_client.folder(folder_id)
        folder_info = folder.get()
        folder_name = folder_info.name
        print(f"✅ Folder accessed: {folder_name}")
        
        files = []
        folder_items = folder.get_items(limit=1000)
        for item in folder_items:
            if item.type == 'file':
                files.append(item)
        
        print(f"✅ Found {len(files)} files in folder")
        
        if not files:
            return {
                'success': False,
                'message': 'No files found in the folder'
            }
        
        # Test Box AI and get working agent
        working_agent, test_result = test_box_ai_with_fallback(box_client, files)
        
        if working_agent:
            print("✅ Found working AI agent, generating full summary...")
            
            # Try to generate summary with all files using working agent
            try:
                auth = box_client.auth
                access_token = auth._access_token
                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                }
                
                ai_items = []
                for file_item in files:
                    ai_items.append({
                        "id": file_item.id,
                        "type": "file"
                    })
                
                # Use working agent for full analysis
                ai_request_payload = {
                    "mode": "multiple_item_qa",
                    "prompt": "Analyze these financial documents and provide a comprehensive summary including account balances, investments, loans, and overall financial position.",
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
                        print("✅ AI analysis completed successfully")
                        summary_data = {
                            "ai_summary": financial_summary,
                            "total_files": len(files),
                            "analysis_method": "Box AI",
                            "generated_on": datetime.now().isoformat()
                        }
                    else:
                        print("⚠️ Empty AI response, using fallback")
                        summary_data = create_fallback_summary(files, folder_name)
                else:
                    print(f"⚠️ AI request failed: {response.status_code}, using fallback")
                    summary_data = create_fallback_summary(files, folder_name)
                    
            except Exception as e:
                print(f"⚠️ Error during AI analysis: {str(e)}, using fallback")
                summary_data = create_fallback_summary(files, folder_name)
        else:
            print("⚠️ No working AI agent found, using fallback summary")
            summary_data = create_fallback_summary(files, folder_name)
        
        # Generate PDF
        try:
            print("📄 Generating PDF...")
            pdf_stream = io.BytesIO()
            doc = SimpleDocTemplate(pdf_stream, pagesize=letter)
            
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle('TitleStyle', 
                                       parent=styles['Heading1'], 
                                       fontSize=18, 
                                       textColor=colors.navy, 
                                       spaceAfter=12, 
                                       alignment=TA_CENTER)
            
            content = []
            content.append(Paragraph("Financial Summary Report", title_style))
            content.append(Paragraph(f"Generated on: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
            content.append(Spacer(1, 20))
            
            # Add summary content
            if "ai_summary" in summary_data:
                content.append(Paragraph("AI Analysis Results", styles['Heading2']))
                # Split long text into paragraphs
                ai_text = summary_data["ai_summary"]
                for paragraph in ai_text.split('\n'):
                    if paragraph.strip():
                        content.append(Paragraph(paragraph.strip(), styles['Normal']))
                        content.append(Spacer(1, 6))
            else:
                content.append(Paragraph("Document Summary", styles['Heading2']))
                content.append(Paragraph(summary_data.get("summary", "No summary available"), styles['Normal']))
                content.append(Spacer(1, 12))
                
                # File list
                content.append(Paragraph("Processed Files", styles['Heading3']))
                for file_info in summary_data.get("files_processed", []):
                    content.append(Paragraph(f"• {file_info['file_name']}", styles['Normal']))
            
            # Add disclaimer
            content.append(Spacer(1, 20))
            disclaimer_style = ParagraphStyle('Disclaimer', 
                                            parent=styles['Normal'], 
                                            fontSize=8, 
                                            textColor=colors.gray)
            content.append(Paragraph(
                "This financial summary is generated based on the documents provided and should be reviewed with a financial professional. "
                "The information contained herein is for informational purposes only and should not be construed as financial advice.",
                disclaimer_style
            ))
            
            doc.build(content)
            pdf_stream.seek(0)
            
            if pdf_stream.getbuffer().nbytes > 0:
                print("✅ PDF generated successfully")
                
                # Upload PDF to Box
                file_name = f"Financial_Summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                new_file = folder.upload_stream(pdf_stream, file_name)
                print(f"✅ PDF uploaded: {new_file.name} (ID: {new_file.id})")
                
                return {
                    'success': True,
                    'message': 'Financial summary generated successfully',
                    'fileId': new_file.id,
                    'fileName': new_file.name,
                    'folderId': folder_id,
                    'format': 'pdf',
                    'summary_data': summary_data
                }
            else:
                return {
                    'success': False,
                    'message': 'PDF generation failed - empty stream'
                }
                
        except Exception as pdf_error:
            print(f"❌ PDF generation failed: {str(pdf_error)}")
            
            # Fallback to text file
            try:
                print("📄 Falling back to text file...")
                text_content = f"FINANCIAL SUMMARY - {folder_name}\n\n"
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
                text_content += "\nDisclaimer: This financial summary should be reviewed with a financial professional."
                
                text_stream = io.BytesIO(text_content.encode('utf-8'))
                file_name = f"Financial_Summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                new_file = folder.upload_stream(text_stream, file_name)
                print(f"✅ Text file uploaded: {new_file.name} (ID: {new_file.id})")
                
                return {
                    'success': True,
                    'message': 'Financial summary generated successfully (text format)',
                    'fileId': new_file.id,
                    'fileName': new_file.name,
                    'folderId': folder_id,
                    'format': 'txt',
                    'summary_data': summary_data
                }
                
            except Exception as text_error:
                print(f"❌ Text file generation also failed: {str(text_error)}")
                return {
                    'success': False,
                    'message': f'Both PDF and text generation failed: {str(text_error)}'
                }
    
    except Exception as e:
        print(f"❌ Overall process failed: {str(e)}")
        print(traceback.format_exc())
        return {
            'success': False,
            'message': f'Financial summary generation failed: {str(e)}'
        }

def main():
    """Test the improved financial summary generation"""
    print("Improved Financial Summary Generation Test")
    print("=" * 50)
    
    folder_id = input("Enter folder ID to test: ").strip()
    if not folder_id:
        print("No folder ID provided")
        return
    
    result = improved_generate_financial_summary(folder_id)
    
    print("\n" + "=" * 50)
    print("RESULT:")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main() 