from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class ClientOnboardingInfo(models.Model):
    """Model to store client onboarding information including address."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='onboarding_info')
    
    # Personal Information
    full_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    
    # Address Information
    street_address = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state_province = models.CharField(max_length=50, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, default='USA')
    
    # Financial Information
    retirement_age = models.IntegerField(null=True, blank=True)
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    risk_tolerance = models.CharField(max_length=20, choices=[
        ('conservative', 'Conservative'),
        ('moderate', 'Moderate'),
        ('aggressive', 'Aggressive')
    ], blank=True)
    investment_goals = models.JSONField(default=list, blank=True)  # Store as list of goals
    investment_timeframe = models.CharField(max_length=20, choices=[
        ('short', 'Short-term (0-3 years)'),
        ('medium', 'Medium-term (3-10 years)'),
        ('long', 'Long-term (10+ years)')
    ], blank=True)
    investable_assets = models.CharField(max_length=20, choices=[
        ('under100k', 'Under $100,000'),
        ('100k-250k', '$100,000 - $250,000'),
        ('250k-500k', '$250,000 - $500,000'),
        ('500k-1m', '$500,000 - $1,000,000'),
        ('1m-5m', '$1,000,000 - $5,000,000'),
        ('over5m', 'Over $5,000,000')
    ], blank=True)
    special_considerations = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.full_name}"
    
    @property
    def full_address(self):
        """Return the complete address as a string."""
        address_parts = []
        if self.street_address:
            address_parts.append(self.street_address)
        if self.city:
            address_parts.append(self.city)
        if self.state_province:
            address_parts.append(self.state_province)
        if self.postal_code:
            address_parts.append(self.postal_code)
        return ', '.join(address_parts)


class AddressMismatch(models.Model):
    """Model to track address mismatches between client-provided and extracted addresses."""
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='address_mismatches')
    file_id = models.CharField(max_length=100)  # Box file ID
    file_name = models.CharField(max_length=200)
    
    # Client's stored address
    client_street = models.CharField(max_length=200, blank=True)
    client_city = models.CharField(max_length=100, blank=True)
    client_state = models.CharField(max_length=50, blank=True)
    client_postal_code = models.CharField(max_length=20, blank=True)
    client_full_address = models.TextField(blank=True)
    
    # Extracted address from document
    extracted_street = models.CharField(max_length=200, blank=True)
    extracted_city = models.CharField(max_length=100, blank=True)
    extracted_state = models.CharField(max_length=50, blank=True)
    extracted_postal_code = models.CharField(max_length=20, blank=True)
    extracted_full_address = models.TextField(blank=True)
    
    # Mismatch details
    mismatch_type = models.CharField(max_length=50, choices=[
        ('full_mismatch', 'Complete Address Mismatch'),
        ('partial_mismatch', 'Partial Address Mismatch'),
        ('not_validated', 'Address Not Validated')
    ])
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.client.username} - {self.file_name} - {self.mismatch_type}"

    class Meta:
        unique_together = ['client', 'file_id']  # Prevent duplicate mismatches for same file
