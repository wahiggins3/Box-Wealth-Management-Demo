"""
Address Comparison Service

This service handles comparing extracted addresses from documents
against client-provided addresses in the onboarding process.
"""

import logging
from difflib import SequenceMatcher
from django.contrib.auth.models import User
from core.models import ClientOnboardingInfo, AddressMismatch

logger = logging.getLogger(__name__)


class AddressComparisonService:
    """Service for comparing extracted addresses with client addresses."""
    
    @staticmethod
    def normalize_address_component(component):
        """Normalize an address component for comparison."""
        if not component:
            return ""
        
        # Convert to lowercase and strip whitespace
        normalized = str(component).lower().strip()
        
        # Remove common punctuation
        normalized = normalized.replace(',', '').replace('.', '').replace('#', 'apt ')
        
        # Standardize apartment/unit indicators
        normalized = normalized.replace('apartment', 'apt').replace('unit', 'apt').replace('suite', 'ste')
        
        # Remove extra whitespace
        normalized = ' '.join(normalized.split())
        
        return normalized
    
    @staticmethod
    def calculate_similarity(str1, str2):
        """Calculate similarity between two strings using SequenceMatcher."""
        if not str1 and not str2:
            return 1.0  # Both empty, perfect match
        if not str1 or not str2:
            return 0.0  # One empty, no match
        
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    @staticmethod
    def compare_address_components(client_info, extracted_address):
        """Compare individual address components and return similarity scores."""
        comparisons = {}
        
        # Get client address components
        client_components = {
            'street_address': AddressComparisonService.normalize_address_component(client_info.street_address),
            'city': AddressComparisonService.normalize_address_component(client_info.city),
            'state_province': AddressComparisonService.normalize_address_component(client_info.state_province),
            'postal_code': AddressComparisonService.normalize_address_component(client_info.postal_code)
        }
        
        # Get extracted address components
        extracted_components = {
            'street_address': AddressComparisonService.normalize_address_component(extracted_address.get('street_address', '')),
            'city': AddressComparisonService.normalize_address_component(extracted_address.get('city', '')),
            'state_province': AddressComparisonService.normalize_address_component(extracted_address.get('state_province', '')),
            'postal_code': AddressComparisonService.normalize_address_component(extracted_address.get('postal_code', ''))
        }
        
        # Compare each component
        for component in client_components.keys():
            client_val = client_components[component]
            extracted_val = extracted_components[component]
            
            similarity = AddressComparisonService.calculate_similarity(client_val, extracted_val)
            comparisons[component] = {
                'client_value': client_val,
                'extracted_value': extracted_val,
                'similarity': similarity,
                'match': similarity >= 0.8  # Consider 80%+ similarity as a match
            }
        
        return comparisons
    
    @staticmethod
    def determine_mismatch_type(comparisons):
        """Determine the type of address mismatch based on component comparisons."""
        matching_components = sum(1 for comp in comparisons.values() if comp['match'])
        total_components = len(comparisons)
        
        if matching_components == total_components:
            return None  # No mismatch
        elif matching_components == 0:
            return 'full_mismatch'
        else:
            return 'partial_mismatch'
    
    @staticmethod
    def compare_addresses(user, extracted_address, file_id, file_name):
        """
        Compare extracted address with client's stored address.
        
        Args:
            user: Django User object
            extracted_address: Dict containing extracted address components
            file_id: Box file ID
            file_name: Name of the file
            
        Returns:
            Dict with comparison results and mismatch information
        """
        try:
            # Get client onboarding info
            try:
                client_info = ClientOnboardingInfo.objects.get(user=user)
            except ClientOnboardingInfo.DoesNotExist:
                logger.warning(f"No onboarding info found for user {user.username}")
                return {
                    'success': False,
                    'message': 'No client address information found for comparison',
                    'mismatch_created': False
                }
            
            # Check if client has any address information
            if not any([client_info.street_address, client_info.city, client_info.state_province, client_info.postal_code]):
                logger.warning(f"No address information stored for user {user.username}")
                return {
                    'success': False,
                    'message': 'No client address information available for comparison',
                    'mismatch_created': False
                }
            
            # Compare address components
            comparisons = AddressComparisonService.compare_address_components(client_info, extracted_address)
            
            # Determine mismatch type
            mismatch_type = AddressComparisonService.determine_mismatch_type(comparisons)
            
            result = {
                'success': True,
                'client_address': {
                    'street_address': client_info.street_address,
                    'city': client_info.city,
                    'state_province': client_info.state_province,
                    'postal_code': client_info.postal_code,
                    'full_address': client_info.full_address
                },
                'extracted_address': extracted_address,
                'comparisons': comparisons,
                'mismatch_type': mismatch_type,
                'has_mismatch': mismatch_type is not None,
                'mismatch_created': False
            }
            
            # If there's a mismatch, create or update a mismatch record
            if mismatch_type:
                mismatch, created = AddressMismatch.objects.update_or_create(
                    client=user,
                    file_id=file_id,
                    defaults={
                        'file_name': file_name,
                        'client_street': client_info.street_address,
                        'client_city': client_info.city,
                        'client_state': client_info.state_province,
                        'client_postal_code': client_info.postal_code,
                        'client_full_address': client_info.full_address,
                        'extracted_street': extracted_address.get('street_address', ''),
                        'extracted_city': extracted_address.get('city', ''),
                        'extracted_state': extracted_address.get('state_province', ''),
                        'extracted_postal_code': extracted_address.get('postal_code', ''),
                        'extracted_full_address': extracted_address.get('full_address', ''),
                        'mismatch_type': mismatch_type,
                        'resolved': False
                    }
                )
                
                result['mismatch_created'] = created
                result['mismatch_updated'] = not created
                
                logger.info(f"Address mismatch {'created' if created else 'updated'} for user {user.username}, file {file_name}")
            else:
                # Address matches, remove any existing mismatch record
                deleted_count, _ = AddressMismatch.objects.filter(client=user, file_id=file_id).delete()
                if deleted_count > 0:
                    logger.info(f"Removed resolved address mismatch for user {user.username}, file {file_name}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error comparing addresses for user {user.username}: {e}")
            return {
                'success': False,
                'message': f'Error comparing addresses: {str(e)}',
                'mismatch_created': False
            }
    
    @staticmethod
    def get_user_address_mismatches(user):
        """Get all unresolved address mismatches for a user."""
        try:
            mismatches = AddressMismatch.objects.filter(client=user, resolved=False).order_by('-created_at')
            return list(mismatches)
        except Exception as e:
            logger.error(f"Error getting address mismatches for user {user.username}: {e}")
            return [] 