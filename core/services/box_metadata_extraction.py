"""
Box Metadata Extraction Service

This module handles extracting metadata from Box files using the Box AI Skills.
"""
import logging
import time
import json
from django.conf import settings
from boxsdk.exception import BoxAPIException

logger = logging.getLogger(__name__)

class BoxMetadataExtractionService:
    """Service for extracting metadata from Box files."""
    
    def __init__(self, box_client):
        """Initialize with an authenticated Box client.
        
        Args:
            box_client: An authenticated Box client instance
        """
        self.client = box_client
    
    def extract_base_metadata(self, file_id):
        """Extract financialDocumentBase metadata from a file.
        
        Args:
            file_id: Box file ID to extract metadata from
            
        Returns:
            dict: The result of the operation with extracted metadata
        """
        try:
            logger.info(f"========== STARTING BASE METADATA EXTRACTION ==========")
            logger.info(f"Extracting base metadata from file {file_id}")
            
            # First, verify the file exists
            try:
                file_obj = self.client.file(file_id)
                file_info = file_obj.get()
                logger.info(f"File exists: {file_info.name} (ID: {file_id})")
            except Exception as e:
                logger.error(f"Error accessing file {file_id}: {e}")
                return {'success': False, 'message': f'File not found or inaccessible: {str(e)}'}
            
            # Try the Box AI extraction
            try:
                # Use Box's financialDocumentBase extraction template
                logger.info(f"Attempting to extract metadata using Box AI for file {file_id}")
                extraction_result = self._extract_with_box_ai(file_id, 'financialDocumentBase')
                
                if extraction_result['success']:
                    logger.info(f"Box AI extraction successful for file {file_id}")
                    # Log the extracted metadata
                    metadata = extraction_result.get('data', {})
                    logger.info(f"Extracted metadata: {json.dumps(metadata, indent=2)}")
                    
                    # Check if this is actually extracted data or just template definitions
                    if self._is_template_definition(metadata):
                        logger.warning(f"Box AI returned template definition instead of extracted data for file {file_id}")
                        # Fall back to our fallback extraction method
                        fallback_result = self._extract_base_metadata_fallback(file_id, file_info)
                        logger.info(f"Using fallback extraction due to template definition response: {json.dumps(fallback_result, indent=2)}")
                        return fallback_result
                    
                    return extraction_result
                
                # If Box AI failed, try our fallback extraction method
                logger.warning(f"Box AI extraction failed, trying fallback: {extraction_result['message']}")
                fallback_result = self._extract_base_metadata_fallback(file_id, file_info)
                logger.info(f"Fallback extraction result: {json.dumps(fallback_result, indent=2)}")
                return fallback_result
                
            except Exception as e:
                logger.error(f"Error in Box AI extraction for file {file_id}: {e}")
                fallback_result = self._extract_base_metadata_fallback(file_id, file_info)
                logger.info(f"Fallback extraction result after exception: {json.dumps(fallback_result, indent=2)}")
                return fallback_result
                
        except Exception as e:
            logger.error(f"Error extracting base metadata from file {file_id}: {e}")
            return {'success': False, 'message': str(e)}
        finally:
            logger.info(f"========== FINISHED BASE METADATA EXTRACTION ==========")
    
    def extract_document_type_metadata(self, file_id, document_type):
        """Extract document-specific metadata from a file.
        
        Args:
            file_id: Box file ID to extract metadata from
            document_type: Document type to determine which template to use
            
        Returns:
            dict: The result of the operation with extracted metadata
        """
        try:
            logger.info(f"========== STARTING {document_type} METADATA EXTRACTION ==========")
            logger.info(f"Extracting {document_type} metadata from file {file_id}")
            
            # Map document_type to template_key
            template_key = self._get_template_key_for_document_type(document_type)
            if not template_key:
                logger.warning(f"No template found for document type: {document_type}")
                return {'success': False, 'message': f'No template for {document_type}'}
            
            logger.info(f"Using template key: {template_key} for document type: {document_type}")
            
            # Try the Box AI extraction with the specific template
            try:
                extraction_result = self._extract_with_box_ai(file_id, template_key)
                
                if extraction_result['success']:
                    logger.info(f"Box AI extraction successful for {document_type} (file {file_id})")
                    # Log the extracted metadata
                    metadata = extraction_result.get('data', {})
                    logger.info(f"Extracted document-specific metadata: {json.dumps(metadata, indent=2)}")
                    return extraction_result
                
                # If Box AI failed, use fallback
                logger.warning(f"Box AI extraction failed for {document_type}, using fallback")
                fallback_result = self._extract_document_type_fallback(file_id, document_type)
                logger.info(f"Fallback document-specific extraction result: {json.dumps(fallback_result, indent=2)}")
                return fallback_result
                
            except Exception as e:
                logger.error(f"Error in Box AI extraction for {document_type} (file {file_id}): {e}")
                fallback_result = self._extract_document_type_fallback(file_id, document_type)
                logger.info(f"Fallback document-specific extraction result after exception: {json.dumps(fallback_result, indent=2)}")
                return fallback_result
                
        except Exception as e:
            logger.error(f"Error extracting {document_type} metadata from file {file_id}: {e}")
            return {'success': False, 'message': str(e)}
        finally:
            logger.info(f"========== FINISHED {document_type} METADATA EXTRACTION ==========")

    def extract_address_validation_metadata(self, file_id):
        """Extract address validation metadata from a file.
        
        Args:
            file_id: Box file ID to extract metadata from
            
        Returns:
            dict: The result of the operation with extracted metadata
        """
        try:
            logger.info(f"========== STARTING ADDRESS VALIDATION METADATA EXTRACTION ==========")
            logger.info(f"Extracting address validation metadata from file {file_id}")
            
            # First, verify the file exists
            try:
                file_obj = self.client.file(file_id)
                file_info = file_obj.get()
                logger.info(f"File exists: {file_info.name} (ID: {file_id})")
            except Exception as e:
                logger.error(f"Error accessing file {file_id}: {e}")
                return {'success': False, 'message': f'File not found or inaccessible: {str(e)}'}
            
            # Try the Box AI extraction with address_validation template
            try:
                logger.info(f"Attempting to extract address metadata using Box AI for file {file_id}")
                extraction_result = self._extract_with_box_ai(file_id, 'address_validation')
                
                if extraction_result['success']:
                    logger.info(f"Box AI address extraction successful for file {file_id}")
                    # Log the extracted metadata
                    metadata = extraction_result.get('data', {})
                    logger.info(f"Extracted address metadata: {json.dumps(metadata, indent=2)}")
                    
                    # Add extraction date if not present
                    if 'date_extracted' not in metadata or not metadata['date_extracted']:
                        from datetime import datetime
                        metadata['date_extracted'] = datetime.now().strftime('%Y-%m-%d')
                        logger.info(f"Added extraction date: {metadata['date_extracted']}")
                    
                    extraction_result['data'] = metadata
                    return extraction_result
                
                # If Box AI failed, try our fallback extraction method
                logger.warning(f"Box AI address extraction failed, trying fallback: {extraction_result['message']}")
                fallback_result = self._extract_address_validation_fallback(file_id, file_info)
                logger.info(f"Fallback address extraction result: {json.dumps(fallback_result, indent=2)}")
                return fallback_result
                
            except Exception as e:
                logger.error(f"Error in Box AI address extraction for file {file_id}: {e}")
                # Fall back to simpler extraction
                fallback_result = self._extract_address_validation_fallback(file_id, file_info)
                logger.info(f"Fallback address extraction result after exception: {json.dumps(fallback_result, indent=2)}")
                return fallback_result
                
        except Exception as e:
            logger.error(f"Error extracting address validation metadata from file {file_id}: {e}")
            return {'success': False, 'message': str(e)}
        finally:
            logger.info(f"========== FINISHED ADDRESS VALIDATION METADATA EXTRACTION ==========")
    
    def _extract_with_box_ai(self, file_id, template_key):
        """Extract metadata from a file using Box AI.
        
        Args:
            file_id: Box file ID to extract metadata from
            template_key: The metadata template key to use
            
        Returns:
            dict: The result of the operation with extracted metadata
        """
        try:
            logger.info(f"========== STARTING BOX AI EXTRACTION FOR FILE ID: {file_id} ==========")
            logger.info(f"Performing Box AI extraction for file {file_id} with template {template_key}")
            
            # Get the file object
            file_obj = self.client.file(file_id)
            
            # Use the Box AI API endpoint for structured metadata extraction
            url = 'https://api.box.com/2.0/ai/extract_structured'
            
            # Define the request body based on Box API documentation
            data = {
                'items': [{
                    'id': file_id,
                    'type': 'file'
                }],
                'ai_agent': {
                    'type': 'ai_agent_extract_structured',
                    'long_text': {
                        'model': 'azure__openai__gpt_4o_mini'
                    },
                    'basic_text': {
                        'model': 'azure__openai__gpt_4o_mini'
                    }
                }
            }
            
            # For address_validation and other custom templates, use field definitions
            # For existing Box templates like financialDocumentBase, use template reference
            if template_key == 'address_validation':
                # For address validation, we need to use our custom field definitions
                # since this template is not a built-in Box template
                template_fields = self._get_template_fields(template_key)
                if template_fields:
                    logger.info(f"Using specific fields configuration for extraction")
                    data['fields'] = template_fields
                else:
                    logger.error(f"No field configuration found for template {template_key}")
                    return {'success': False, 'message': f'No field configuration for template {template_key}', 'file_id': file_id}
            else:
                # For built-in Box templates like financialDocumentBase, use metadata_template reference
                # This is more reliable as it uses Box's existing template definitions
                logger.info(f"Using metadata template reference for extraction")
                data['metadata_template'] = {
                    'template_key': template_key,
                    'type': 'metadata_template',
                    'scope': 'enterprise_218068865'
                }
            
            logger.info(f"Sending extraction request to Box AI for file ID {file_id}: {json.dumps(data, indent=2)}")
            
            # Make the API request directly using post
            try:
                # Ensure data is properly serialized as JSON
                json_data = json.dumps(data)
                headers = {'Content-Type': 'application/json'}
                response = self.client.make_request('POST', url, data=json_data, headers=headers)
                response_json = response.json()
                logger.info(f"Box AI extraction response for file ID {file_id}: {json.dumps(response_json, indent=2)}")
                
                # Check if extraction was successful
                if response.status_code in [200, 202]:
                    logger.info(f"Extraction request successful for file {file_id}")
                    
                    # Process the response based on the structure from Box AI API
                    if 'fields' in response_json and isinstance(response_json['fields'], list):
                        # Handle structured fields response format (expected from Box AI structured extract)
                        logger.info(f"Received structured fields response for file ID {file_id}")
                        field_dict = {}
                        for field in response_json['fields']:
                            if 'key' in field and 'value' in field:
                                field_dict[field['key']] = field['value']
                        
                        logger.info(f"Extracted metadata fields for file ID {file_id}: {json.dumps(field_dict, indent=2)}")
                        return {
                            'success': True,
                            'message': 'Metadata extraction completed successfully',
                            'data': field_dict,
                            'file_id': file_id
                        }
                    elif 'entries' in response_json and len(response_json['entries']) > 0:
                        # Handle legacy format (if still supported)
                        extraction_result = response_json['entries'][0]
                        metadata = extraction_result.get('metadata', {})
                        logger.info(f"Extracted metadata from entries for file ID {file_id}: {json.dumps(metadata, indent=2)}")
                        return {
                            'success': True,
                            'message': 'Metadata extraction completed successfully',
                            'data': metadata,
                            'file_id': file_id
                        }
                    elif 'completion_reason' in response_json and 'ai_agent_info' in response_json:
                        # This is a Box AI structured extraction response but without fields
                        # We need to check if the template was correctly applied or if there are other fields in the response
                        logger.info(f"Received Box AI structured extract response without explicit fields for file ID {file_id}")
                        
                        # The AI response might include the extracted data as top-level keys or in a specific format
                        # Look for fields that could be meaningful data (not metadata about the response)
                        extracted_data = {}
                        excluded_fields = ['ai_agent_info', 'completion_reason', 'created_at', 'type', 'id', 'scope', 'template']
                        
                        # First look for answer field which might contain the structured data
                        if 'answer' in response_json:
                            if isinstance(response_json['answer'], dict):
                                # Check if the answer contains fields with template definitions vs actual values
                                if 'fields' in response_json['answer'] and isinstance(response_json['answer']['fields'], list):
                                    # This might be a template definition response - check if fields have values
                                    has_values = any('value' in field for field in response_json['answer']['fields'])
                                    if has_values:
                                        # Extract the values
                                        for field in response_json['answer']['fields']:
                                            if 'key' in field and 'value' in field:
                                                extracted_data[field['key']] = field['value']
                                    else:
                                        # This is a template definition, not extracted data
                                        logger.warning(f"Box AI returned template definition instead of extracted data for file {file_id}")
                                        logger.warning(f"Template definition fields: {[field.get('key', 'unknown') for field in response_json['answer']['fields']]}")
                                        # Fall back to using fallback extraction
                                        return {'success': False, 'message': 'Box AI returned template definition instead of extracted data', 'file_id': file_id}
                                else:
                                    # Direct answer dict with extracted values
                                    extracted_data = response_json['answer']
                            elif isinstance(response_json['answer'], str):
                                try:
                                    # Try to parse answer as JSON if it's a string
                                    parsed_answer = json.loads(response_json['answer'])
                                    if isinstance(parsed_answer, dict):
                                        extracted_data = parsed_answer
                                except json.JSONDecodeError:
                                    # If not JSON, just store as text
                                    extracted_data = {'extracted_text': response_json['answer']}
                        
                        # If no answer field found, extract all relevant fields from top level
                        if not extracted_data:
                            extracted_data = {k: v for k, v in response_json.items() 
                                           if k not in excluded_fields and not k.startswith('$')}
                        
                        logger.info(f"Extracted data from AI response for file ID {file_id}: {json.dumps(extracted_data, indent=2)}")
                        return {
                            'success': True,
                            'message': 'Metadata extraction completed successfully with AI',
                            'data': extracted_data,
                            'file_id': file_id
                        }
                    
                    # If response format is not recognized, return the whole response for debugging
                    logger.warning(f"Unexpected response format for file ID {file_id}, returning full response for debugging")
                    return {
                        'success': True,
                        'message': 'Extraction completed with unknown format',
                        'data': response_json,
                        'file_id': file_id
                    }
                else:
                    logger.error(f"Extraction request failed for file ID {file_id}: {response.status_code} - {response.text}")
                    return {
                        'success': False,
                        'message': f'Extraction request failed: {response.status_code} - {response.text}',
                        'file_id': file_id
                    }
            except Exception as api_error:
                logger.error(f"API error in Box extraction for file ID {file_id}: {api_error}")
                return {'success': False, 'message': f'API error: {str(api_error)}', 'file_id': file_id}
            
        except Exception as e:
            logger.error(f"Error in Box AI extraction for file ID {file_id}: {e}")
            return {'success': False, 'message': str(e), 'file_id': file_id}
        finally:
            logger.info(f"========== FINISHED BOX AI EXTRACTION FOR FILE ID: {file_id} ==========")
    
    def extract_with_custom_request(self, file_id, request_data):
        """Extract metadata from a file using Box AI with custom request data.
        
        Args:
            file_id: Box file ID to extract metadata from
            request_data: Custom request data for the Box AI API
            
        Returns:
            dict: The result of the operation with extracted metadata
        """
        try:
            logger.info(f"========== STARTING BOX AI EXTRACTION WITH CUSTOM REQUEST FOR FILE ID: {file_id} ==========")
            
            # Get the file object to verify it exists
            file_obj = self.client.file(file_id)
            file_info = file_obj.get()
            logger.info(f"File exists: {file_info.name} (ID: {file_id})")
            
            # Use the Box AI API endpoint for structured metadata extraction
            url = 'https://api.box.com/2.0/ai/extract_structured'
            
            # If the ai_agent.type is incorrect, update it to the correct value
            if isinstance(request_data, dict) and 'ai_agent' in request_data and 'type' in request_data['ai_agent']:
                if request_data['ai_agent']['type'] != 'ai_agent_extract_structured':
                    logger.info(f"Updating ai_agent.type from '{request_data['ai_agent']['type']}' to 'ai_agent_extract_structured'")
                    request_data['ai_agent']['type'] = 'ai_agent_extract_structured'
                    
            # Print the full request data for debugging
            if isinstance(request_data, dict):
                logger.info(f"Using custom request data: {json.dumps(request_data, indent=2)}")
            
            # Make the API request directly using post
            try:
                # Ensure request_data is properly serialized as JSON
                headers = {'Content-Type': 'application/json'}
                
                if isinstance(request_data, dict):
                    # Convert the request data to a JSON string manually to ensure proper formatting
                    json_data = json.dumps(request_data)
                    response = self.client.make_request('POST', url, data=json_data, headers=headers)
                else:
                    # If already a string, use as is with headers
                    response = self.client.make_request('POST', url, data=request_data, headers=headers)
                
                response_json = response.json()
                logger.info(f"Box AI extraction response for file ID {file_id}: {json.dumps(response_json, indent=2)}")
                
                # Check if extraction was successful
                if response.status_code in [200, 202]:
                    logger.info(f"Extraction request successful for file {file_id}")
                    
                    # Process the response based on the structure from Box AI API
                    if 'fields' in response_json:
                        # Handle structured fields response format
                        logger.info(f"Received structured fields response for file ID {file_id}")
                        field_dict = {}
                        for field in response_json['fields']:
                            if 'key' in field and 'value' in field:
                                field_dict[field['key']] = field['value']
                        
                        logger.info(f"Extracted metadata fields for file ID {file_id}: {json.dumps(field_dict, indent=2)}")
                        return {
                            'success': True,
                            'message': 'Metadata extraction completed successfully',
                            'data': field_dict,
                            'file_id': file_id
                        }
                    elif 'entries' in response_json and len(response_json['entries']) > 0:
                        # Handle legacy format (if still supported)
                        extraction_result = response_json['entries'][0]
                        metadata = extraction_result.get('metadata', {})
                        logger.info(f"Extracted metadata from entries for file ID {file_id}: {json.dumps(metadata, indent=2)}")
                        return {
                            'success': True,
                            'message': 'Metadata extraction completed successfully',
                            'data': metadata,
                            'file_id': file_id
                        }
                    elif 'completion_reason' in response_json:
                        # Handle new Box AI API response format
                        # The actual data might be in different locations based on the AI response
                        extracted_data = {}
                        
                        # Check if there's an 'answer' field or similar that contains the structured data
                        if 'answer' in response_json:
                            extracted_data = response_json['answer']
                        elif 'ai_agent_info' in response_json:
                            # This might contain other useful information
                            logger.info(f"AI agent info for file ID {file_id}: {json.dumps(response_json['ai_agent_info'], indent=2)}")
                            # The actual data might be in the root of the response
                            extracted_data = {k: v for k, v in response_json.items() 
                                           if k not in ['ai_agent_info', 'completion_reason', 'created_at']}
                        
                        logger.info(f"Extracted data from AI response for file ID {file_id}: {json.dumps(extracted_data, indent=2)}")
                        return {
                            'success': True,
                            'message': 'Metadata extraction completed successfully with AI',
                            'data': extracted_data,
                            'file_id': file_id
                        }
                    
                    # If response format is not recognized, return the whole response
                    logger.warning(f"Unexpected response format for file ID {file_id}, attempting to extract metadata directly")
                    return {
                        'success': True,
                        'message': 'Extraction completed with unknown format',
                        'data': response_json,
                        'file_id': file_id
                    }
                else:
                    logger.error(f"Extraction request failed for file ID {file_id}: {response.status_code} - {response.text}")
                    return {
                        'success': False,
                        'message': f'Extraction request failed: {response.status_code} - {response.text}',
                        'file_id': file_id
                    }
            except Exception as api_error:
                logger.error(f"API error in Box extraction for file ID {file_id}: {api_error}")
                return {'success': False, 'message': f'API error: {str(api_error)}', 'file_id': file_id}
            
        except Exception as e:
            logger.error(f"Error in Box AI extraction with custom request for file ID {file_id}: {e}")
            return {'success': False, 'message': str(e), 'file_id': file_id}
        finally:
            logger.info(f"========== FINISHED BOX AI EXTRACTION WITH CUSTOM REQUEST FOR FILE ID: {file_id} ==========")
    
    def _poll_extraction_status(self, extraction_id, max_attempts=10, delay_seconds=2):
        """Poll for the status of a metadata extraction operation.
        
        Args:
            extraction_id: The ID of the extraction operation
            max_attempts: Maximum number of polling attempts
            delay_seconds: Delay between polling attempts
            
        Returns:
            dict: The result of the extraction operation
        """
        try:
            # Define the status endpoint
            url = f'https://api.box.com/2.0/metadata_templates/extraction/{extraction_id}'
            
            for attempt in range(max_attempts):
                logger.info(f"Polling attempt {attempt + 1}/{max_attempts} for extraction {extraction_id}")
                
                # Wait before polling
                time.sleep(delay_seconds)
                
                # Make the request
                response = self.client.make_request('GET', url)
                
                if response.status_code == 200:
                    # Parse the response
                    status_info = response.json()
                    status = status_info.get('status')
                    
                    logger.info(f"Extraction status: {status}")
                    
                    if status == 'success':
                        logger.info(f"Extraction {extraction_id} completed successfully")
                        metadata = status_info.get('metadata', {})
                        return {'success': True, 'message': 'Extraction completed', 'data': metadata}
                    elif status == 'pending':
                        logger.info(f"Extraction {extraction_id} still in progress")
                        continue
                    else:
                        logger.warning(f"Extraction {extraction_id} failed with status: {status}")
                        return {'success': False, 'message': f'Extraction failed with status: {status}'}
                else:
                    logger.error(f"Error polling extraction status: {response.status_code} - {response.text}")
            
            # If we've reached the maximum number of attempts
            return {'success': False, 'message': f'Extraction timed out after {max_attempts} attempts'}
            
        except Exception as e:
            logger.error(f"Error polling extraction status: {e}")
            return {'success': False, 'message': str(e)}
    
    def _extract_base_metadata_fallback(self, file_id, file_info):
        """Fallback method for extracting base metadata when Box AI fails.
        
        Args:
            file_id: Box file ID
            file_info: Box file info object
            
        Returns:
            dict: The extraction result
        """
        try:
            logger.info(f"Using fallback extraction for file {file_id}")
            
            # Extract filename for basic info
            filename = file_info.name.lower()
            logger.info(f"Analyzing filename: {filename}")
            
            # Basic document type detection based on filename
            document_type = None
            if '1099' in filename:
                document_type = '1099'
            elif 'w-2' in filename or 'w2' in filename:
                document_type = 'W-2'
            elif 'statement' in filename and ('account' in filename or 'bank' in filename or 'brokerage' in filename):
                document_type = 'Account Statement'
            elif 'mortgage' in filename:
                document_type = 'Mortgage Statement'
            elif 'trust' in filename:
                document_type = 'Trust Document'
            elif 'asset' in filename and 'list' in filename:
                document_type = 'Asset List'
            elif '1040' in filename:
                document_type = '1040'
            elif 'financial' in filename and 'statement' in filename:
                document_type = 'Personal Financial Statement'
            elif 'insurance' in filename:
                document_type = 'Life Insurance Document'
            else:
                document_type = 'Unknown'
            
            # Create basic metadata
            metadata = {
                'documentType': document_type,
                'documentDate': None,
                'issuerName': None,
                'recipientName': None
            }
            
            logger.info(f"Fallback identified document type as {document_type} for file {file_id}")
            logger.info(f"Generated fallback metadata: {json.dumps(metadata, indent=2)}")
            return {
                'success': True,
                'message': 'Fallback metadata extraction completed',
                'data': metadata
            }
            
        except Exception as e:
            logger.error(f"Error in fallback extraction: {e}")
            return {'success': False, 'message': str(e)}
    
    def _extract_document_type_fallback(self, file_id, document_type):
        """Fallback method for extracting document-specific metadata when Box AI fails.
        
        Args:
            file_id: Box file ID
            document_type: Document type
            
        Returns:
            dict: The extraction result
        """
        try:
            logger.info(f"Using fallback extraction for {document_type} (file {file_id})")
            
            # Create empty metadata based on document type
            metadata = {}
            
            if document_type == '1099':
                metadata = {
                    'payerName': None,
                    'payerTIN': None,
                    'recipientTIN': None,
                    'nonemployeeCompensation': None
                }
            elif document_type == 'W-2':
                metadata = {
                    'employerEIN': None,
                    'wagesAndTips': None,
                    'federalIncomeTaxWithheld': None,
                    'socialSecurityWages': None
                }
            elif document_type == 'Account Statement':
                metadata = {
                    'accountNumber': None,
                    'statementDate': None,
                    'beginningBalance': None,
                    'endingBalance': None
                }
            # Add more document types as needed
            
            logger.info(f"Fallback created basic metadata structure for {document_type} (file {file_id})")
            logger.info(f"Generated document-specific fallback metadata: {json.dumps(metadata, indent=2)}")
            return {
                'success': True,
                'message': 'Fallback document-specific metadata created',
                'data': metadata
            }
            
        except Exception as e:
            logger.error(f"Error in document-specific fallback extraction: {e}")
            return {'success': False, 'message': str(e)}
    
    def _get_template_key_for_document_type(self, document_type):
        """Map document type to appropriate template key.
        
        Args:
            document_type: Document type from financialDocumentBase
            
        Returns:
            str: Template key or None if no mapping exists
        """
        # Map from document_type value to template_key
        template_map = {
            "1099": "irs1099",
            "W-2": "irsw2",
            "Account Statement": "accountStatement",
            "Mortgage Statement": "mortgageStatement",
            "Trust Document": "trustDocument",
            "Asset List": "assetList",
            "1040": "irs1040",
            "Personal Financial Statement": "personalFinancialStatement",
            "Life Insurance Document": "lifeInsuranceDocument",
            "Other": "otherDocument"  # Added for documents that don't fit existing categories
        }
        
        template_key = template_map.get(document_type)
        if template_key:
            logger.info(f"Mapped document type '{document_type}' to template key '{template_key}'")
        else:
            # If no mapping found, use the 'Other' category
            logger.warning(f"No template key mapping found for document type '{document_type}', using 'otherDocument' template")
            template_key = "otherDocument"
        
        return template_key
    
    def _get_template_fields(self, template_key):
        """Get the fields configuration for a specific template key.
        
        Args:
            template_key: The metadata template key
            
        Returns:
            list: The fields configuration for structured extraction
        """
        # Define the fields for each template based on metadata_template_reference.md
        if template_key == 'financialDocumentBase':
            return [
                {
                    "key": "documentType",
                    "displayName": "Document Type",
                    "description": "The type of financial document",
                    "type": "enum",
                    "options": [
                        {"key": "1099"}, 
                        {"key": "W-2"},
                        {"key": "Account Statement"},
                        {"key": "Mortgage Statement"},
                        {"key": "Trust Document"},
                        {"key": "Asset List"},
                        {"key": "1040"},
                        {"key": "Personal Financial Statement"},
                        {"key": "Life Insurance Document"},
                        {"key": "Other"}
                    ]
                },
                {
                    "key": "taxYear",
                    "displayName": "Tax Year",
                    "description": "The tax year the document applies to",
                    "type": "date"
                },
                {
                    "key": "issuerName",
                    "displayName": "Issuer Name",
                    "description": "The organization or entity that issued the document",
                    "type": "string"
                },
                {
                    "key": "recipientName",
                    "displayName": "Recipient Name",
                    "description": "The person or entity receiving the document",
                    "type": "string"
                },
                {
                    "key": "documentDate",
                    "displayName": "Document Date",
                    "description": "The date on the document",
                    "type": "date"
                },
                {
                    "key": "accountOrPolicyNoMasked",
                    "displayName": "Account/Policy Number (Masked)",
                    "description": "The masked account or policy number",
                    "type": "string"
                },
                {
                    "key": "isLegible",
                    "displayName": "Is Legible",
                    "description": "Whether the document is legible and readable",
                    "type": "enum",
                    "options": [
                        {"key": "Yes"},
                        {"key": "No"}
                    ]
                }
            ]
        elif template_key == 'address_validation':
            return [
                {
                    "key": "street_address",
                    "displayName": "Street Address",
                    "description": "Street number, name, and optional unit number of the address",
                    "type": "string"
                },
                {
                    "key": "city",
                    "displayName": "City",
                    "description": "City associated with the address",
                    "type": "string"
                },
                {
                    "key": "state_province",
                    "displayName": "State/Province",
                    "description": "Two-letter abbreviation of the state or province",
                    "type": "string"
                },
                {
                    "key": "postal_code",
                    "displayName": "Postal Code",
                    "description": "ZIP code or postal code of the address",
                    "type": "string"
                },
                {
                    "key": "country",
                    "displayName": "Country",
                    "description": "Country of the address",
                    "type": "string"
                },
                {
                    "key": "full_address",
                    "displayName": "Full Address",
                    "description": "Concatenated full address for quick comparison",
                    "type": "string"
                },
                {
                    "key": "validation_status",
                    "displayName": "Validation Status",
                    "description": "Indicates whether the extracted address matches the record address",
                    "type": "enum",
                    "options": [
                        {"key": "Match"},
                        {"key": "Mismatch"},
                        {"key": "Partial Match"},
                        {"key": "Not Validated"}
                    ]
                },
                {
                    "key": "date_extracted",
                    "displayName": "Date Extracted",
                    "description": "Date when the address was extracted",
                    "type": "date"
                }
            ]
        elif template_key == 'irs1099':
            return [
                {
                    "key": "formVariant",
                    "displayName": "Form Variant",
                    "description": "The specific variant of 1099 form",
                    "type": "enum",
                    "options": [
                        {"key": "INT"},
                        {"key": "DIV"},
                        {"key": "B"},
                        {"key": "MISC"},
                        {"key": "NEC"}
                    ]
                },
                {
                    "key": "payerTinMasked",
                    "displayName": "Payer TIN (Masked)",
                    "description": "The payer's Tax Identification Number (masked)",
                    "type": "string"
                },
                {
                    "key": "recipientTinMasked",
                    "displayName": "Recipient TIN (Masked)",
                    "description": "The recipient's Tax Identification Number (masked)",
                    "type": "string"
                },
                {
                    "key": "box1IncomeAmount",
                    "displayName": "Box 1 Income Amount",
                    "description": "The amount in Box 1 of the 1099 form",
                    "type": "float"
                },
                {
                    "key": "federalTaxWithheld",
                    "displayName": "Federal Tax Withheld",
                    "description": "The amount of federal tax withheld",
                    "type": "float"
                }
            ]
        elif template_key == 'irsw2':
            return [
                {
                    "key": "employerEinMasked",
                    "displayName": "Employer EIN (Masked)",
                    "description": "The employer's EIN number (masked)",
                    "type": "string"
                },
                {
                    "key": "employeeSsnMasked",
                    "displayName": "Employee SSN (Masked)",
                    "description": "The employee's SSN (masked)",
                    "type": "string"
                },
                {
                    "key": "box1Wages",
                    "displayName": "Box 1 Wages",
                    "description": "The wages amount in Box 1",
                    "type": "float"
                },
                {
                    "key": "box2FederalWithholding",
                    "displayName": "Box 2 Federal Withholding",
                    "description": "The federal income tax withheld amount in Box 2",
                    "type": "float"
                }
            ]
        elif template_key == 'accountStatement':
            return [
                {
                    "key": "institutionName",
                    "displayName": "Institution Name",
                    "description": "The financial institution name",
                    "type": "string"
                },
                {
                    "key": "accountType",
                    "displayName": "Account Type",
                    "description": "The type of financial account",
                    "type": "enum",
                    "options": [
                        {"key": "Checking"},
                        {"key": "Savings"},
                        {"key": "Brokerage"}
                    ]
                }
            ]
            
        # For other templates or if not found, return None to use default behavior
        return None 

    def _extract_address_validation_fallback(self, file_id, file_info):
        """Fallback method for extracting address validation metadata when Box AI fails.
        
        Args:
            file_id: Box file ID
            file_info: File information object
            
        Returns:
            dict: Fallback metadata extraction result
        """
        try:
            logger.info(f"Creating fallback address validation metadata for file {file_id}")
            
            from datetime import datetime
            
            # Create basic fallback metadata
            metadata = {
                'street_address': '',
                'city': '',
                'state_province': '',
                'postal_code': '',
                'country': 'US',  # Default to US
                'full_address': '',
                'validation_status': 'Not Validated',
                'date_extracted': datetime.now().strftime('%Y-%m-%d')
            }
            
            logger.info(f"Generated address validation fallback metadata: {json.dumps(metadata, indent=2)}")
            return {
                'success': True,
                'message': 'Fallback address validation metadata created',
                'data': metadata
            }
            
        except Exception as e:
            logger.error(f"Error in address validation fallback extraction: {e}")
            return {'success': False, 'message': str(e)} 
    
    def _is_template_definition(self, metadata):
        """Check if the metadata contains template definitions instead of extracted values.
        
        Args:
            metadata: The extracted metadata from Box AI
            
        Returns:
            bool: True if it's a template definition, False if it's extracted data
        """
        if not isinstance(metadata, dict):
            return False
            
        # Check if it has 'fields' array with template definitions
        if 'fields' in metadata and isinstance(metadata['fields'], list):
            # Check if any field has 'prompt' and 'type' but no 'value'
            for field in metadata['fields']:
                if isinstance(field, dict) and 'prompt' in field and 'type' in field and 'value' not in field:
                    logger.info(f"Found template definition field: {field.get('key', 'unknown')}")
                    return True
        
        # Check for other template definition indicators
        template_indicators = ['template_key', 'ai_agent_info', 'completion_reason']
        if any(key in metadata for key in template_indicators):
            logger.info(f"Found template definition indicators: {[key for key in template_indicators if key in metadata]}")
            return True
            
        # Check if all values are None or empty (another indicator of template definitions)
        if all(value in [None, '', []] for value in metadata.values() if not isinstance(value, dict)):
            logger.info("All metadata values are empty, likely a template definition")
            return True
            
        return False 