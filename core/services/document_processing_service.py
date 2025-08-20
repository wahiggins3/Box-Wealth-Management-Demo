"""
Document Processing Service

This module orchestrates the document processing workflow, including:
1. Metadata extraction using Box AI
2. Applying extracted metadata back to the file
"""
import logging
from django.conf import settings
from .box_metadata_extraction import BoxMetadataExtractionService
from .box_metadata_application import BoxMetadataApplicationService

logger = logging.getLogger(__name__)

class DocumentProcessingService:
    """Service for processing uploaded documents through extraction and metadata application."""
    
    def __init__(self, box_client):
        """Initialize with an authenticated Box client.
        
        Args:
            box_client: An authenticated Box client instance
        """
        self.client = box_client
        self.extraction_service = BoxMetadataExtractionService(box_client)
        self.metadata_service = BoxMetadataApplicationService(box_client)
    
    def process_uploaded_document(self, file_id, file_name=None):
        """Process a newly uploaded document.
        
        Args:
            file_id: Box file ID to process
            file_name: Original file name (optional)
            
        Returns:
            dict: Result of the processing operation
        """
        try:
            logger.info(f"Processing uploaded document {file_id}")
            
            # Step 1: Extract base metadata
            base_metadata_result = self.extraction_service.extract_base_metadata(file_id)
            if not base_metadata_result:
                logger.error(f"Failed to extract base metadata for {file_id}")
                return {
                    'success': False, 
                    'message': 'Base metadata extraction failed',
                    'file_id': file_id
                }
            
            # Step 2: Apply base metadata to the file
            base_apply_result = self.metadata_service.apply_base_metadata(
                file_id, 
                base_metadata_result
            )
            
            # Step 3: Determine document type from extracted metadata
            document_type = self._get_document_type_from_metadata(base_metadata_result)
            
            if not document_type:
                logger.warning(f"Could not determine document type for {file_id}")
                return {
                    'success': True,
                    'message': 'Applied base metadata only, could not determine document type',
                    'file_id': file_id,
                    'base_metadata': base_apply_result
                }
            
            # Step 4: Extract document-type specific metadata
            type_metadata_result = self.extraction_service.extract_document_type_metadata(
                file_id,
                document_type
            )
            
            # Step 5: Apply document-type specific metadata
            if type_metadata_result:
                type_apply_result = self.metadata_service.apply_document_type_metadata(
                    file_id,
                    document_type,
                    type_metadata_result
                )
                
                logger.info(f"Successfully processed document {file_id} with type {document_type}")
                return {
                    'success': True,
                    'message': f'Successfully processed document with type {document_type}',
                    'file_id': file_id,
                    'document_type': document_type,
                    'base_metadata': base_apply_result,
                    'type_metadata': type_apply_result
                }
            else:
                logger.warning(f"Document type extraction failed for {file_id} with type {document_type}")
                return {
                    'success': True,
                    'message': 'Applied base metadata only, document type extraction failed',
                    'file_id': file_id,
                    'document_type': document_type,
                    'base_metadata': base_apply_result
                }
                
        except Exception as e:
            logger.error(f"Error processing document {file_id}: {e}")
            return {
                'success': False,
                'message': f'Document processing error: {str(e)}',
                'file_id': file_id
            }
    
    def process_batch(self, file_ids):
        """Process a batch of documents.
        
        Args:
            file_ids: List of Box file IDs to process
            
        Returns:
            list: Results for each processed file
        """
        results = []
        for file_id in file_ids:
            result = self.process_uploaded_document(file_id)
            results.append(result)
        return results
    
    def _get_document_type_from_metadata(self, metadata_result):
        """Extract document type from metadata result.
        
        Args:
            metadata_result: Metadata extraction result
            
        Returns:
            str: Document type or None if not found
        """
        if not metadata_result:
            return None
            
        # Extract from answer if available
        if isinstance(metadata_result, dict):
            if 'answer' in metadata_result and isinstance(metadata_result['answer'], dict):
                answer = metadata_result['answer']
                if 'documentType' in answer:
                    return answer['documentType']
            
            # Direct access if it's at the top level
            if 'documentType' in metadata_result:
                return metadata_result['documentType']
                
            # Look through fields array if present
            if 'fields' in metadata_result and isinstance(metadata_result['fields'], list):
                for field in metadata_result['fields']:
                    if field.get('key') == 'documentType' and 'value' in field:
                        return field['value']
        
        return None 