"""
Box Metadata Application Service

This module handles applying extracted metadata back to Box files.
"""
import logging
import json
from django.conf import settings
# Import only the correct Box exception class
from boxsdk.exception import BoxAPIException
from boxsdk.object.metadata_template import MetadataTemplate

logger = logging.getLogger(__name__)

class BoxMetadataApplicationService:
    """Service for applying metadata to Box files."""
    
    def __init__(self, box_client):
        """Initialize with an authenticated Box client.
        
        Args:
            box_client: An authenticated Box client instance
        """
        self.client = box_client
    
    def apply_base_metadata(self, file_id, extracted_metadata):
        """Apply financialDocumentBase metadata to a file.
        
        Args:
            file_id: Box file ID to apply metadata to
            extracted_metadata: The metadata to apply
            
        Returns:
            dict: The result of the operation
        """
        try:
            # Extract the actual metadata from the extraction result if needed
            metadata_values = self._extract_metadata_values(extracted_metadata)
            
            # Log the extracted metadata in a clean format
            if metadata_values:
                logger.info(f"📄 METADATA TO APPLY for file {file_id}:")
                for field, value in metadata_values.items():
                    if value:  # Only log fields with values
                        logger.info(f"  {field}: {value}")
            else:
                logger.info(f"  No metadata values to apply for file {file_id}")
            
            # Step 1: Try only with critical fields first (minimal approach to ensure success)
            critical_fields = ['documentType', 'isLegible']
            critical_metadata = {k: v for k, v in metadata_values.items() if k in critical_fields and v is not None and v != ""}
            
            if critical_metadata and 'documentType' in critical_metadata:
                critical_result = self._apply_metadata(
                    file_id, 
                    'financialDocumentBase', 
                    critical_metadata,
                    'enterprise_218068865'
                )
                
                if critical_result.get('success', False):
                    logger.info(f"✅ CRITICAL METADATA APPLIED successfully")
                    
                    # If critical fields succeeded, try to apply the secondary fields separately
                    secondary_fields = [
                        'issuerName', 'recipientName', 'accountOrPolicyNoMasked'
                    ]
                    
                    secondary_metadata = {k: v for k, v in metadata_values.items() 
                                         if k in secondary_fields and v is not None and v != ""}
                    
                    if secondary_metadata:
                        logger.info(f"📊 APPLYING SECONDARY METADATA:")
                        for field, value in secondary_metadata.items():
                            logger.info(f"  {field}: {value}")
                        
                        secondary_result = self._apply_metadata(
                            file_id, 
                            'financialDocumentBase', 
                            secondary_metadata,
                            'enterprise_218068865'
                        )
                        
                        if secondary_result.get('success', False):
                            logger.info(f"✅ SECONDARY METADATA APPLIED successfully")
                            # Return the complete updated metadata
                            return {
                                'success': True, 
                                'message': 'Successfully applied metadata in phases',
                                'data': {**critical_metadata, **secondary_metadata}
                            }
                    
                    # Even if secondary fields failed, we've successfully applied critical fields
                    return critical_result
            
            # Step 2: If critical fields approach didn't work or we don't have documentType, 
            # try the standard approach with all fields
            
            # Only include fields from the template, but try without date fields first
            template_fields = [
                'documentType', 'issuerName', 'recipientName', 
                'accountOrPolicyNoMasked', 'isLegible'
            ]
            
            filtered_metadata = {k: v for k, v in metadata_values.items() 
                               if k in template_fields and v is not None and v != ""}
            
            if filtered_metadata:
                logger.info(f"📄 APPLYING STANDARD METADATA:")
                for field, value in filtered_metadata.items():
                    logger.info(f"  {field}: {value}")
            
            # Apply the metadata without date fields
            result = self._apply_metadata(
                file_id, 
                'financialDocumentBase', 
                filtered_metadata,
                'enterprise_218068865'
            )
            
            if result.get('success', False):
                logger.info(f"✅ STANDARD METADATA APPLIED successfully")
                return result
            else:
                logger.info(f"❌ Standard metadata application failed")
                return result
            
        except Exception as e:
            logger.info(f"❌ Error applying base metadata to file {file_id}")
            return {'success': False, 'message': str(e)}
    
    def apply_document_type_metadata(self, file_id, document_type, extracted_metadata):
        """Apply document-specific metadata to a file.
        
        Args:
            file_id: Box file ID to apply metadata to
            document_type: Document type to determine which template to use
            extracted_metadata: The metadata to apply
            
        Returns:
            dict: The result of the operation
        """
        try:
            logger.info(f"📋 APPLYING {document_type} METADATA for file {file_id}")
            
            # Map document_type to template_key
            template_key = self._get_template_key_for_document_type(document_type)
            if not template_key:
                logger.info(f"❓ No template found for document type: {document_type}")
                return {'success': False, 'message': f'No template for {document_type}'}
            
            if not extracted_metadata:
                logger.info(f"❓ No metadata to apply to file {file_id}")
                return {'success': False, 'message': 'No metadata to apply'}
            
            # Extract the actual metadata from the extraction result if needed
            metadata_values = self._extract_metadata_values(extracted_metadata)
            
            # Log the extracted metadata in a clean format
            if metadata_values:
                logger.info(f"📄 {document_type} METADATA TO APPLY:")
                for field, value in metadata_values.items():
                    if value:  # Only log fields with values
                        logger.info(f"  {field}: {value}")
            else:
                logger.info(f"  No {document_type} metadata values to apply")
            
            # Get template field types to understand what we're dealing with
            field_types = self._get_template_field_types(template_key, 'enterprise_218068865')
            
            # First, try applying only non-numeric fields as those are less likely to cause validation issues
            numeric_field_keys = []
            non_numeric_fields = {}
            
            for field_key, field_value in metadata_values.items():
                if field_key in field_types and field_types[field_key] in ['float', 'int']:
                    numeric_field_keys.append(field_key)
                else:
                    non_numeric_fields[field_key] = field_value
            
            # Apply non-numeric fields first
            if non_numeric_fields:
                logger.info(f"📊 APPLYING NON-NUMERIC {document_type} FIELDS:")
                for field, value in non_numeric_fields.items():
                    logger.info(f"  {field}: {value}")
                
                non_numeric_result = self._apply_metadata(
                    file_id, 
                    template_key, 
                    non_numeric_fields,
                    'enterprise_218068865'
                )
                
                if non_numeric_result.get('success', False):
                    logger.info(f"✅ NON-NUMERIC {document_type} METADATA APPLIED successfully")
                else:
                    logger.info(f"❌ Non-numeric {document_type} metadata application failed")
            
            # Then apply numeric fields individually to avoid validation issues
            numeric_fields = {k: v for k, v in metadata_values.items() if k in numeric_field_keys}
            success_count = 0
            for field_key, field_value in numeric_fields.items():
                logger.info(f"📊 APPLYING NUMERIC FIELD: {field_key} = {field_value}")
                
                single_field_result = self._apply_metadata(
                    file_id,
                    template_key,
                    {field_key: field_value},
                    'enterprise_218068865'
                )
                
                if single_field_result.get('success', False):
                    logger.info(f"✅ NUMERIC FIELD {field_key} APPLIED successfully")
                    success_count += 1
                else:
                    logger.info(f"❌ NUMERIC FIELD {field_key} application failed: {single_field_result.get('message', 'Unknown error')}")
            
            # Return final result
            if non_numeric_fields or numeric_fields:
                overall_success = (non_numeric_result.get('success', True) if non_numeric_fields else True) and \
                                (success_count == len(numeric_fields) if numeric_fields else True)
                
                message = f"{document_type} metadata applied"
                if numeric_fields:
                    message += f" ({success_count}/{len(numeric_fields)} numeric fields successful)"
                    
                return {
                    'success': overall_success,
                    'message': message,
                    'non_numeric_result': non_numeric_result if non_numeric_fields else None,
                    'numeric_success_count': success_count,
                    'numeric_total': len(numeric_fields)
                }
            else:
                return {'success': False, 'message': 'No valid metadata fields to apply'}
                
        except Exception as e:
            logger.error(f"Error applying {document_type} metadata to file {file_id}: {e}")
            return {'success': False, 'message': str(e)}

    def apply_address_validation_metadata(self, file_id, extracted_metadata):
        """Apply address validation metadata to a file.
        
        Args:
            file_id: Box file ID to apply metadata to
            extracted_metadata: The metadata to apply
            
        Returns:
            dict: The result of the operation
        """
        try:
            logger.info(f"📋 APPLYING ADDRESS VALIDATION METADATA for file {file_id}")
            
            if not extracted_metadata:
                logger.info(f"❓ No address metadata to apply to file {file_id}")
                return {'success': False, 'message': 'No address metadata to apply'}
            
            # Extract the actual metadata from the extraction result if needed
            metadata_values = self._extract_metadata_values(extracted_metadata)
            
            # Log the extracted metadata in a clean format
            if metadata_values:
                logger.info(f"📄 ADDRESS VALIDATION METADATA TO APPLY:")
                for field, value in metadata_values.items():
                    if value:  # Only log fields with values
                        logger.info(f"  {field}: {value}")
            else:
                logger.info(f"  No address validation metadata values to apply")
                return {'success': False, 'message': 'No valid address metadata values to apply'}
            
            # Build full address if components are available and full_address is not set
            if not metadata_values.get('full_address') and any(metadata_values.get(field) for field in ['street_address', 'city', 'state_province', 'postal_code']):
                address_parts = []
                if metadata_values.get('street_address'):
                    address_parts.append(metadata_values['street_address'])
                if metadata_values.get('city'):
                    address_parts.append(metadata_values['city'])
                if metadata_values.get('state_province'):
                    address_parts.append(metadata_values['state_province'])
                if metadata_values.get('postal_code'):
                    address_parts.append(metadata_values['postal_code'])
                
                metadata_values['full_address'] = ', '.join(address_parts)
                logger.info(f"Built full address: {metadata_values['full_address']}")
            
            logger.info(f"📋 CALLING _apply_metadata with template 'address_validation' and {len(metadata_values)} fields")
            
            # Apply the address validation metadata
            result = self._apply_metadata(
                file_id, 
                'address_validation', 
                metadata_values,
                'enterprise_218068865'
            )
            
            logger.info(f"📋 _apply_metadata returned: success={result.get('success', False)}, message='{result.get('message', 'No message')}'")
            
            if result.get('success', False):
                logger.info(f"✅ ADDRESS VALIDATION METADATA APPLIED successfully")
                return {
                    'success': True,
                    'message': 'Address validation metadata applied successfully',
                    'data': metadata_values
                }
            else:
                error_message = result.get('message', 'Unknown error')
                logger.error(f"❌ Address validation metadata application failed: {error_message}")
                logger.error(f"Full application result: {result}")
                return {
                    'success': False,
                    'message': f"Address validation metadata application failed: {error_message}",
                    'details': result
                }
                
        except Exception as e:
            logger.error(f"Error applying address validation metadata to file {file_id}: {e}")
            return {'success': False, 'message': str(e)}
    
    def _extract_metadata_values(self, extraction_result):
        """Extract metadata values from an extraction result.
        
        Args:
            extraction_result: The extraction result to extract metadata from
            
        Returns:
            dict: The extracted metadata values
        """
        # If extraction_result is already a dict with direct key-value pairs, use it
        if isinstance(extraction_result, dict) and not any(k in ['success', 'message', 'data', 'file_id'] for k in extraction_result):
            logger.info("Using extraction result directly as metadata")
            return extraction_result
            
        # If it's a success/message/data structure, extract the data
        if isinstance(extraction_result, dict):
            # Check if it has a data field which is often used in our response format
            if 'data' in extraction_result and isinstance(extraction_result['data'], dict):
                logger.info("Extracted metadata from 'data' field")
                return extraction_result['data']
            
            # Handle new Box AI structured extraction format
            if 'ai_agent_info' in extraction_result:
                logger.info("Detected Box AI structured extraction response")
                
                # Extract fields with values from the response
                if 'fields' in extraction_result and isinstance(extraction_result['fields'], list):
                    logger.info("Processing Box AI 'fields' list")
                    field_dict = {}
                    for field in extraction_result['fields']:
                        if 'key' in field and 'value' in field:
                            field_dict[field['key']] = field['value']
                            logger.info(f"  Found field with value: {field['key']} = {field['value']}")
                        elif 'key' in field and 'prompt' in field:
                            # This is a template definition, not extracted data
                            logger.warning(f"  Field is template definition, not extracted data: {field['key']}")
                        else:
                            logger.warning(f"  Field missing value: {field}")
                    
                    if field_dict:
                        logger.info(f"Extracted metadata from Box AI 'fields' list: {json.dumps(field_dict, indent=2)}")
                        return field_dict
                    else:
                        logger.warning("No fields with values found in 'fields' array - this appears to be a template definition, not extracted data")
                        return {}
                
                # Check for answer field
                if 'answer' in extraction_result:
                    if isinstance(extraction_result['answer'], dict):
                        # Check if answer contains template definitions vs actual values
                        if 'fields' in extraction_result['answer'] and isinstance(extraction_result['answer']['fields'], list):
                            logger.info("Processing 'answer.fields' list")
                            field_dict = {}
                            for field in extraction_result['answer']['fields']:
                                if 'key' in field and 'value' in field:
                                    field_dict[field['key']] = field['value']
                                    logger.info(f"  Found field with value: {field['key']} = {field['value']}")
                                elif 'key' in field and 'prompt' in field:
                                    # This is a template definition, not extracted data
                                    logger.warning(f"  Field is template definition, not extracted data: {field['key']}")
                            
                            if field_dict:
                                logger.info(f"Extracted metadata from answer.fields: {json.dumps(field_dict, indent=2)}")
                                return field_dict
                            else:
                                logger.warning("No fields with values found in answer.fields - this appears to be a template definition, not extracted data")
                                return {}
                        else:
                            # Direct answer object with key-value pairs
                            logger.info("Extracted metadata from 'answer' field (dict)")
                            return extraction_result['answer']
                    elif isinstance(extraction_result['answer'], str):
                        try:
                            # Try to parse answer as JSON if it's a string
                            parsed_answer = json.loads(extraction_result['answer'])
                            if isinstance(parsed_answer, dict):
                                logger.info("Extracted metadata from 'answer' field (parsed JSON)")
                                return parsed_answer
                        except json.JSONDecodeError:
                            # If not JSON, just store as text
                            logger.info("Using 'answer' field as text")
                            return {'extracted_text': extraction_result['answer']}
                
                # Try to get relevant data from the response (excluding metadata fields)
                excluded_fields = ['ai_agent_info', 'completion_reason', 'created_at', 'type', 'id', 'scope', 'template', 'success', 'message', 'file_id']
                metadata = {k: v for k, v in extraction_result.items() 
                           if k not in excluded_fields and not k.startswith('$')}
                
                if metadata:
                    logger.info(f"Extracted metadata from AI response: {json.dumps(metadata, indent=2)}")
                    return metadata
                else:
                    logger.warning("No extractable metadata found in Box AI response")
                    return {}
            
            # If there's a "fields" list, convert to dict
            if 'fields' in extraction_result and isinstance(extraction_result['fields'], list):
                logger.info("Processing 'fields' list")
                field_dict = {}
                for field in extraction_result['fields']:
                    if 'key' in field and 'value' in field:
                        field_dict[field['key']] = field['value']
                        logger.info(f"  Found field with value: {field['key']} = {field['value']}")
                    elif 'key' in field and 'prompt' in field:
                        # This is a template definition, not extracted data
                        logger.warning(f"  Field is template definition, not extracted data: {field['key']}")
                    else:
                        logger.warning(f"  Field missing value: {field}")
                
                if field_dict:
                    logger.info(f"Extracted metadata from 'fields' list: {json.dumps(field_dict, indent=2)}")
                    return field_dict
                else:
                    logger.warning("No fields with values found in 'fields' array - Box AI may have returned template definitions instead of extracted data")
                    return {}
            
            # If we have "metadata" field (old format)
            if 'metadata' in extraction_result:
                logger.info("Extracted metadata from 'metadata' field")
                return extraction_result['metadata']
            
            # If nothing else, return any fields that aren't internal metadata
            cleaned_result = {k: v for k, v in extraction_result.items() 
                             if k not in ['success', 'message', 'file_id', 'type', 'id', 'scope', 'template'] 
                             and not k.startswith('$')}
            
            if cleaned_result:
                logger.info(f"Using cleaned extraction result as metadata: {json.dumps(cleaned_result, indent=2)}")
                return cleaned_result
            else:
                logger.warning("No extractable metadata found in extraction result")
                return {}
        
        # If it's not a dict, just return empty dict
        logger.warning(f"Cannot extract metadata from type {type(extraction_result).__name__}")
        return {}
    
    def _verify_template_exists(self, template_key, scope='enterprise'):
        """Verify that a metadata template exists in Box.
        
        Args:
            template_key: Metadata template key
            scope: Metadata scope
            
        Returns:
            bool: Whether the template exists
        """
        try:
            logger.info(f"Verifying template exists: {template_key} in scope {scope}")
            # Get all templates for the enterprise
            templates = self.client.metadata_templates()
            for template in templates:
                if template.templateKey == template_key and template.scope == scope:
                    logger.info(f"Template found: {template_key} in scope {scope}")
                    return True
            
            logger.warning(f"Template not found: {template_key} in scope {scope}")
            return False
        except Exception as e:
            logger.error(f"Error verifying template existence: {e}")
            return False
    
    def _get_template_field_types(self, template_key, scope='enterprise'):
        """Get the field types for a metadata template.
        
        Args:
            template_key: The metadata template key
            scope: The scope of the template
            
        Returns:
            dict: A mapping of field keys to their types
        """
        try:
            # Use direct API to get template details
            enterprise_id = scope.replace('enterprise_', '') if scope.startswith('enterprise_') else scope
            url = f'https://api.box.com/2.0/metadata_templates/{scope}/{template_key}/schema'
            
            response = self.client.make_request('GET', url)
            template_schema = response.json()
            
            field_types = {}
            if 'fields' in template_schema:
                for field in template_schema['fields']:
                    if 'key' in field and 'type' in field:
                        field_types[field['key']] = field['type']
                        logger.info(f"Field {field['key']} has type {field['type']}")
            
            return field_types
        except Exception as e:
            logger.warning(f"Error getting template field types: {e}")
            return {}
    
    def _sanitize_metadata(self, metadata: dict, field_types: dict, template_key: str) -> dict:
        """Return a copy of *metadata* whose values conform to the types in *field_types*.

        Args:
            metadata: Raw key/value pairs extracted from Box AI.
            field_types: Mapping of field‐key → Box type (string, enum, date, float, int …) fetched via the template schema.
            template_key: The template we’re sanitising for – used for enum special-cases.
        """

        sanitized: dict[str, object] = {}

        for key, value in metadata.items():
            # Skip empty / null values outright
            if value in (None, ""):
                continue

            # Unknown fields are silently skipped – Box will reject them otherwise
            field_type = field_types.get(key, "string")

            # --- DATE -----------------------------------------------------
            if field_type == 'date':
                logger.info(f"SANITIZING-DATE: Processing date field '{key}' with value '{value}'")
                try:
                    # Expects YYYY-MM-DD from AI, convert to RFC3339 for Box API
                    if isinstance(value, str) and len(value) == 10 and value[4] == '-' and value[7] == '-':
                        from datetime import datetime
                        dt_obj = datetime.strptime(value, '%Y-%m-%d')
                        sanitized[key] = dt_obj.strftime('%Y-%m-%dT00:00:00Z')
                        logger.info(f"SANITIZING-DATE: Converted date '{key}' to '{sanitized[key]}'")
                    else:
                        logger.warning(f"SANITIZING-DATE: Skipping date '{key}': unexpected format '{value}'")
                except (ValueError, TypeError) as e:
                    logger.warning(f"SANITIZING-DATE: Skipping date '{key}': parsing error '{e}'")

            # --- ENUM -----------------------------------------------------
            elif field_type == 'enum':
                if template_key == 'address_validation' and key == 'validation_status':
                    valid_statuses = ['Match', 'Mismatch', 'Partial Match', 'Not Validated']
                    sanitized[key] = value if value in valid_statuses else 'Not Validated'
                else:
                    sanitized[key] = str(value)

            # --- NUMBER ---------------------------------------------------
            elif field_type in ('float', 'number', 'int'):
                try:
                    sanitized[key] = float(value)
                except Exception:
                    logger.warning(f"SANITIZE: Could not cast '{key}' value '{value}' to float – keeping as string")
                    sanitized[key] = str(value)

            # --- DEFAULT STRING ------------------------------------------
            else:
                sanitized[key] = str(value)

        return sanitized

    def _apply_metadata(self, file_id, template_key, metadata, scope='enterprise'):
        """Apply metadata to a file using Box API with proper JSON Patch format for updates."""
        try:
            actual_scope = 'enterprise_218068865'
            
            logger.info(f"APPLY-META: Applying metadata for file {file_id}, template {template_key}")
            
            # Fetch template schema to know the field types
            field_types = self._get_template_field_types(template_key, actual_scope)

            # Sanitize metadata before applying
            sanitized_metadata = self._sanitize_metadata(metadata, field_types, template_key)
            if not sanitized_metadata:
                logger.warning(f"APPLY-META: No valid metadata to apply for file {file_id} after sanitization.")
                return {'success': True, 'message': 'No valid metadata to apply.'}

            logger.info(f"APPLY-META: Sanitized metadata: {json.dumps(sanitized_metadata, indent=2)}")

            # First, attempt to create the metadata instance using POST
            url = f'https://api.box.com/2.0/files/{file_id}/metadata/{actual_scope}/{template_key}'
            logger.info(f"APPLY-META: POST {url}")
            
            try:
                headers = {'Content-Type': 'application/json'}
                response = self.client.make_request('POST', url, data=json.dumps(sanitized_metadata), headers=headers)
                
                if 200 <= response.status_code < 300:
                    result = response.json()
                    logger.info(f"APPLY-META: CREATED new metadata instance for file {file_id}")
                    return {'success': True, 'data': result, 'message': 'Metadata created successfully'}
                elif response.status_code == 409:
                    # 409 means metadata already exists, try update
                    logger.info(f"APPLY-META: Metadata already exists (409), attempting update")
                else:
                    # For other errors, log and fail
                    error_content = response.content.decode() if response.content else "No content"
                    logger.error(f"APPLY-META: POST failed with status {response.status_code}: {error_content}")
                    return {'success': False, 'message': f"Failed to create metadata: {error_content}"}
                    
            except BoxAPIException as box_error:
                if box_error.status == 409:
                    logger.info(f"APPLY-META: Metadata already exists (BoxAPIException 409), attempting update")
                else:
                    logger.error(f"APPLY-META: POST failed with BoxAPIException: {box_error}")
                    return {'success': False, 'message': f"Failed to create metadata: {box_error}"}
            except Exception as create_error:
                logger.info(f"APPLY-META: POST failed with exception: {create_error}, attempting update")
                
            # If we reach here, metadata exists and we need to update it
            # Convert sanitized metadata to JSON Patch operations using 'add' for new fields
            operations = []
            for key, value in sanitized_metadata.items():
                if value is not None and value != "":
                    # Use 'add' operation which works for both new and existing fields
                    operations.append({
                        'op': 'add',
                        'path': f'/{key}',
                        'value': value
                    })
            
            if not operations:
                logger.warning("APPLY-META: No valid operations to perform")
                return {'success': False, 'message': 'No valid operations to perform'}
            
            logger.info(f"APPLY-META: PUT {url} with JSON Patch operations:")
            for op in operations:
                logger.info(f"  {op['op']} {op['path']} = {op['value']}")
            
            try:
                headers = {'Content-Type': 'application/json-patch+json'}
                response = self.client.make_request('PUT', url, data=json.dumps(operations), headers=headers)
                
                if 200 <= response.status_code < 300:
                    result = response.json()
                    logger.info(f"APPLY-META: UPDATED metadata instance for file {file_id}")
                    return {'success': True, 'data': result, 'message': 'Metadata updated successfully'}
                else:
                    error_content = response.content.decode() if response.content else "No content"
                    logger.error(f"APPLY-META: PUT failed. Status: {response.status_code}, Response: {error_content}")
                    return {'success': False, 'message': f"Failed to update metadata: {error_content}"}
                    
            except Exception as update_error:
                logger.error(f"APPLY-META: Update failed: {update_error}")
                return {'success': False, 'message': f"Failed to update metadata: {update_error}"}

        except Exception as e:
            logger.error(f"APPLY-META: An unexpected error occurred in _apply_metadata: {e}", exc_info=True)
            return {'success': False, 'message': f"An unexpected error occurred: {e}"}
    
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