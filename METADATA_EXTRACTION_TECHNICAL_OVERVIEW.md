# Metadata Extraction and Application Technical Overview

## Table of Contents

- [High-Level Architecture](#high-level-architecture)
- [Workflow Overview](#workflow-overview)
- [Box AI Integration](#box-ai-integration)
- [Metadata Template Structure](#metadata-template-structure)
- [Metadata Application Process](#metadata-application-process)
- [Response Format Processing](#response-format-processing)
- [Error Handling & Fallbacks](#error-handling--fallbacks)
- [Real-World Example](#real-world-example)
- [Performance & Scalability](#performance--scalability)
- [Technical Implementation Details](#technical-implementation-details)

## High-Level Architecture

The system uses a **multi-layered approach** with three main components:

1. **Box AI-powered extraction** via the Box AI API
2. **Structured metadata templates** stored in Box Enterprise
3. **Progressive metadata application** with fallback mechanisms

### Key Components

- **BoxMetadataExtractionService**: Handles AI-powered metadata extraction
- **BoxMetadataApplicationService**: Manages metadata persistence to Box files
- **DocumentProcessingService**: Orchestrates the complete workflow
- **Enterprise Metadata Templates**: Structured schemas for different document types

## Workflow Overview

### Phase 1: File Upload & Template Initialization

1. **File Upload**: Files are uploaded to Box through the web interface
2. **Template Attachment**: The system ensures base metadata templates are attached to files

```python
# From core/views.py:1369-1383
try:
    metadata = file_obj.metadata(scope='enterprise_218068865', template='financialDocumentBase').get()
    logging.info(f"Base metadata template already exists for file {file_id}")
except BoxAPIException as e:
    if e.status == 404:
        # Create empty metadata instance if it doesn't exist
        metadata = file_obj.metadata(scope='enterprise_218068865', template='financialDocumentBase').create({})
        logging.info(f"Applied base metadata template to file {file_id}")
```

### Phase 2: AI-Powered Metadata Extraction

The system uses **Box AI Structured Extraction API** to extract metadata from document content:

```python
# From core/services/box_metadata_extraction.py:210-258
url = 'https://api.box.com/2.0/ai/extract_structured'
data = {
    'items': [{'id': file_id, 'type': 'file'}],
    'ai_agent': {
        'type': 'ai_agent_extract_structured',
        'long_text': {'model': 'azure__openai__gpt_4o_mini'},
        'basic_text': {'model': 'azure__openai__gpt_4o_mini'}
    },
    'metadata_template': {
        'template_key': template_key,
        'type': 'metadata_template',
        'scope': 'enterprise_218068865'
    }
}
```

### Phase 3: Multi-Level Metadata Processing

The extraction follows a **hierarchical approach**:

#### 1. Base Metadata Extraction (`financialDocumentBase` template)
- Document type classification
- Basic document information (issuer, recipient, dates)
- Legibility assessment

#### 2. Document-Specific Metadata (based on identified type)
- **1099 forms** → `irs1099` template
- **W-2 forms** → `irsw2` template  
- **Account Statements** → `accountStatement` template
- **Mortgage Statements** → `mortgageStatement` template
- **Trust Documents** → `trustDocument` template
- **Asset Lists** → `assetList` template
- **1040 forms** → `irs1040` template
- **Personal Financial Statements** → `personalFinancialStatement` template
- **Life Insurance Documents** → `lifeInsurancePolicy` template

#### 3. Address Validation Metadata (`address_validation` template)
- Street address extraction
- City, state, postal code parsing
- Address validation status
- Full address concatenation

## Box AI Integration

### API Endpoint
The system integrates with Box AI using the structured extraction endpoint:
- **URL**: `https://api.box.com/2.0/ai/extract_structured`
- **Method**: POST
- **Authentication**: Box JWT authentication
- **Models**: `azure__openai__gpt_4o_mini` for both long and basic text processing

### Request Structure

#### For Built-in Templates (e.g., financialDocumentBase)
```json
{
  "items": [{"id": "file_id", "type": "file"}],
  "ai_agent": {
    "type": "ai_agent_extract_structured",
    "long_text": {"model": "azure__openai__gpt_4o_mini"},
    "basic_text": {"model": "azure__openai__gpt_4o_mini"}
  },
  "metadata_template": {
    "template_key": "financialDocumentBase",
    "type": "metadata_template",
    "scope": "enterprise_218068865"
  }
}
```

#### For Custom Templates (e.g., address_validation)
```json
{
  "items": [{"id": "file_id", "type": "file"}],
  "ai_agent": {
    "type": "ai_agent_extract_structured",
    "long_text": {"model": "azure__openai__gpt_4o_mini"},
    "basic_text": {"model": "azure__openai__gpt_4o_mini"}
  },
  "fields": [
    {
      "key": "street_address",
      "displayName": "Street Address",
      "description": "Street number, name, and optional unit number",
      "type": "string"
    }
    // ... more field definitions
  ]
}
```

## Metadata Template Structure

The system uses **enterprise-scoped metadata templates** with typed fields. All templates are scoped to `enterprise_218068865`.

### Base Template: financialDocumentBase

```yaml
Template Key: financialDocumentBase
Scope: enterprise_218068865
Fields:
  - documentType (enum): 
    Options: ['1099', 'W-2', 'Account Statement', 'Mortgage Statement', 
             'Trust Document', 'Asset List', '1040', 
             'Personal Financial Statement', 'Life Insurance Document', 'Other']
  - taxYear (date): The tax year the document applies to
  - issuerName (string): Organization that issued the document
  - recipientName (string): Person/entity receiving the document
  - documentDate (date): Date on the document
  - accountOrPolicyNoMasked (string): Masked account/policy number
  - isLegible (enum): ['Yes', 'No'] - Document readability assessment
```

### Document-Specific Templates

#### IRS 1099 Template (irs1099)
```yaml
Fields:
  - formVariant (enum): ['INT', 'DIV', 'B', 'MISC', 'NEC']
  - payerTinMasked (string): Masked payer TIN
  - recipientTinMasked (string): Masked recipient TIN
  - box1IncomeAmount (float): Income amount from Box 1
  - federalTaxWithheld (float): Federal tax withheld amount
  - stateTaxWithheld (float): State tax withheld
  - costBasis (float): Cost basis for securities
  - dateSold (date): Date securities were sold
```

#### Account Statement Template (accountStatement)
```yaml
Fields:
  - institutionName (string): Financial institution name
  - accountType (enum): ['Checking', 'Savings', 'Brokerage', 'Retirement', 'Credit']
  - statementPeriodStart (date): Statement period start date
  - statementPeriodEnd (date): Statement period end date
  - beginningBalance (float): Beginning balance
  - endingBalance (float): Ending balance
  - totalDeposits (float): Total deposits during period
  - totalWithdrawals (float): Total withdrawals during period
  - netChange (float): Net change in balance
```

#### Address Validation Template (address_validation)
```yaml
Fields:
  - street_address (string): Street number, name, and unit
  - city (string): City name
  - state_province (string): State/province abbreviation
  - postal_code (string): ZIP/postal code
  - country (string): Country name
  - full_address (string): Concatenated full address
  - validation_status (enum): ['Match', 'Mismatch', 'Partial Match', 'Not Validated']
  - date_extracted (date): Extraction timestamp
```

## Metadata Application Process

### Writing Metadata Back to Files

The system uses **Box Metadata API** with a sophisticated two-step application strategy:

```python
# From core/services/box_metadata_application.py:587-650
def _apply_metadata(self, file_id, template_key, metadata, scope='enterprise'):
    url = f'https://api.box.com/2.0/files/{file_id}/metadata/{scope}/{template_key}'
    
    # Step 1: Attempt to CREATE new metadata instance (POST)
    try:
        response = self.client.make_request('POST', url, data=json.dumps(metadata))
        if 200 <= response.status_code < 300:
            return {'success': True, 'message': 'Metadata created successfully'}
    except BoxAPIException as e:
        if e.status == 409:  # Metadata already exists
            # Continue to update step
            pass
    
    # Step 2: UPDATE existing metadata using JSON Patch (PUT)
    operations = [
        {'op': 'add', 'path': f'/{key}', 'value': value} 
        for key, value in metadata.items() 
        if value is not None and value != ""
    ]
    
    headers = {'Content-Type': 'application/json-patch+json'}
    response = self.client.make_request('PUT', url, data=json.dumps(operations), headers=headers)
```

### Data Sanitization & Type Safety

Before application, metadata goes through **strict type validation**:

```python
# From core/services/box_metadata_application.py:511-563
def _sanitize_metadata(self, metadata: dict, field_types: dict, template_key: str) -> dict:
    sanitized = {}
    
    for field_key, field_value in metadata.items():
        if field_key not in field_types:
            continue
            
        field_type = field_types[field_key]
        
        if field_type == 'string':
            # Trim whitespace, ensure non-empty
            sanitized[field_key] = str(field_value).strip() if field_value else None
            
        elif field_type == 'float':
            # Parse from string, validate numeric
            try:
                sanitized[field_key] = float(field_value) if field_value is not None else None
            except (ValueError, TypeError):
                logger.warning(f"Invalid float value for {field_key}: {field_value}")
                
        elif field_type == 'date':
            # Convert to ISO format
            sanitized[field_key] = self._convert_to_iso_date(field_value)
            
        elif field_type == 'enum':
            # Validate against template options
            if field_value in template_options.get(field_key, []):
                sanitized[field_key] = field_value
                
    return {k: v for k, v in sanitized.items() if v is not None and v != ""}
```

### Progressive Application Strategy

The system uses a **phased approach** to maximize success rates:

1. **Critical Fields First**: Apply document type and legibility status
2. **Secondary Fields**: Apply remaining metadata fields
3. **Numeric Fields Individually**: Apply float fields one by one to isolate validation errors

```python
# From core/services/box_metadata_application.py:51-120
def apply_base_metadata(self, file_id, extracted_metadata):
    # Step 1: Critical fields (documentType, isLegible)
    critical_fields = ['documentType', 'isLegible']
    critical_metadata = {k: v for k, v in metadata_values.items() 
                        if k in critical_fields and v is not None and v != ""}
    
    if critical_metadata:
        critical_result = self._apply_metadata(file_id, 'financialDocumentBase', 
                                             critical_metadata, 'enterprise_218068865')
        if critical_result.get('success'):
            # Step 2: Secondary fields
            secondary_fields = ['issuerName', 'recipientName', 'accountOrPolicyNoMasked']
            secondary_metadata = {k: v for k, v in metadata_values.items() 
                                if k in secondary_fields and v is not None and v != ""}
            # Apply secondary metadata...
```

## Response Format Processing

The system handles **multiple Box AI response formats** to ensure compatibility:

### 1. Structured Fields Format
```json
{
  "fields": [
    {"key": "documentType", "value": "W-2"},
    {"key": "issuerName", "value": "ABC Corp"}
  ],
  "ai_agent_info": {...},
  "completion_reason": "done"
}
```

### 2. Answer Object Format
```json
{
  "answer": {
    "documentType": "Account Statement",
    "institutionName": "Fidelity",
    "accountType": "Brokerage"
  },
  "ai_agent_info": {...},
  "completion_reason": "done"
}
```

### 3. Direct Response Format
```json
{
  "institutionName": "Fidelity",
  "accountType": "Brokerage",
  "beginningBalance": 88053.95,
  "ai_agent_info": {...},
  "completion_reason": "done"
}
```

### Response Processing Logic

```python
# From core/services/box_metadata_application.py:338-443
def _extract_metadata_values(self, extraction_result):
    if 'fields' in extraction_result and isinstance(extraction_result['fields'], list):
        # Handle structured fields response
        field_dict = {}
        for field in extraction_result['fields']:
            if 'key' in field and 'value' in field:
                field_dict[field['key']] = field['value']
        return field_dict
        
    elif 'answer' in extraction_result:
        # Handle answer object response
        if isinstance(extraction_result['answer'], dict):
            return extraction_result['answer']
        elif isinstance(extraction_result['answer'], str):
            try:
                return json.loads(extraction_result['answer'])
            except json.JSONDecodeError:
                return {'extracted_text': extraction_result['answer']}
                
    elif 'ai_agent_info' in extraction_result:
        # Handle direct response format
        excluded_fields = ['ai_agent_info', 'completion_reason', 'created_at']
        return {k: v for k, v in extraction_result.items() 
                if k not in excluded_fields and not k.startswith('$')}
```

## Error Handling & Fallbacks

The system implements **robust fallback mechanisms** at every level:

### 1. AI Extraction Failure
```python
# Falls back to template-based defaults
def _extract_base_metadata_fallback(self, file_id, file_info):
    fallback_metadata = {
        'documentType': self._guess_document_type_from_filename(file_info.name),
        'issuerName': None,
        'recipientName': None,
        'isLegible': 'Yes'  # Assume legible unless proven otherwise
    }
    return {'success': True, 'data': fallback_metadata}
```

### 2. Template Detection Issues
```python
# Uses document type hints from filenames and content analysis
def _guess_document_type_from_filename(self, filename):
    filename_lower = filename.lower()
    if '1099' in filename_lower:
        return '1099'
    elif 'w-2' in filename_lower or 'w2' in filename_lower:
        return 'W-2'
    elif 'statement' in filename_lower:
        return 'Account Statement'
    # ... more heuristics
    return 'Other'
```

### 3. Metadata Application Errors
```python
# Retries with reduced field sets
def apply_document_type_metadata(self, file_id, document_type, extracted_metadata):
    # First attempt: All non-numeric fields
    non_numeric_result = self._apply_metadata(file_id, template_key, non_numeric_fields)
    
    # Second attempt: Apply numeric fields individually
    for field_key, field_value in numeric_fields.items():
        single_field_result = self._apply_metadata(file_id, template_key, {field_key: field_value})
```

### 4. Field Type Mismatches
```python
# Automatic type conversion with validation
def _convert_to_iso_date(self, date_value):
    if isinstance(date_value, str):
        # Try multiple date formats
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%B %d, %Y']:
            try:
                return datetime.strptime(date_value, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
    return None
```

## Real-World Example

Here's a real processing example from the logs showing successful extraction:

### Input: Brokerage Statement 2024.pdf

### Box AI Request:
```json
{
  "items": [{"id": "1931393027642", "type": "file"}],
  "ai_agent": {
    "type": "ai_agent_extract_structured",
    "long_text": {"model": "azure__openai__gpt_4o_mini"},
    "basic_text": {"model": "azure__openai__gpt_4o_mini"}
  },
  "metadata_template": {
    "template_key": "accountStatement",
    "type": "metadata_template",
    "scope": "enterprise_218068865"
  }
}
```

### Box AI Response:
```json
{
  "answer": {
    "institutionName": "Fidelity",
    "accountType": "Brokerage",
    "statementPeriodStart": "2024-07-01T00:00:00Z",
    "statementPeriodEnd": "2024-07-31T00:00:00Z",
    "beginningBalance": 88053.95,
    "endingBalance": 103351.18,
    "totalDeposits": 9465,
    "totalWithdrawals": -5485,
    "netChange": 15297.23
  },
  "ai_agent_info": {
    "processor": "basic_text",
    "models": [{"name": "google__gemini_2_0_flash_001", "provider": "google"}]
  },
  "created_at": "2025-07-21T12:44:32.76-07:00",
  "completion_reason": "done"
}
```

### Address Validation Follow-up:
```json
{
  "answer": {
    "street_address": "100 Main St.",
    "city": "Boston",
    "state_province": "MA",
    "postal_code": "02201",
    "full_address": "100 Main St., Boston, MA 02201",
    "validation_status": "Not Validated",
    "date_extracted": "July 21, 2025"
  }
}
```

### Result: Address Mismatch Detection
```
⚠️ ADDRESS MISMATCH DETECTED (full_mismatch)
  Client address: 123 Financial St, Apt 4B, New York, NY, 10001
  Extracted address: 100 Main St., Boston, MA 02201
```

## Performance & Scalability

### Parallel Processing
For batch operations, the system uses **ThreadPoolExecutor** for concurrent processing:

```python
# From core/views.py:1916-1953
def process_documents_metadata_batch(request):
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_single_file, file_id) for file_id in file_ids]
        results = []
        for future in as_completed(futures):
            try:
                result = future.result(timeout=300)  # 5 minute timeout per file
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing file: {e}")
```

### Processing Statistics
From the real-world example:
- **Total files**: 6
- **Successful**: 6 (100%)
- **Failed**: 0
- **Processing time**: 40.24 seconds
- **Average per file**: ~6.7 seconds

### Optimization Strategies

1. **Template Reuse**: Templates are cached and reused across files
2. **Batched Operations**: Multiple files processed in parallel
3. **Progressive Enhancement**: Critical metadata applied first
4. **Selective Field Application**: Only populated fields are sent to Box API
5. **Response Format Detection**: Automatic adaptation to different AI response formats

## Technical Implementation Details

### Key Classes and Methods

#### BoxMetadataExtractionService
- `extract_base_metadata(file_id)`: Extracts financialDocumentBase metadata
- `extract_document_type_metadata(file_id, document_type)`: Extracts type-specific metadata
- `extract_address_validation_metadata(file_id)`: Extracts address information
- `_extract_with_box_ai(file_id, template_key)`: Core Box AI integration method

#### BoxMetadataApplicationService
- `apply_base_metadata(file_id, metadata)`: Applies base template metadata
- `apply_document_type_metadata(file_id, doc_type, metadata)`: Applies type-specific metadata
- `apply_address_validation_metadata(file_id, metadata)`: Applies address metadata
- `_apply_metadata(file_id, template_key, metadata, scope)`: Core metadata application method

### Security Considerations

1. **Enterprise Scope**: All metadata uses enterprise-specific scope (`enterprise_218068865`)
2. **Field Masking**: Sensitive data (SSNs, account numbers) are automatically masked
3. **Type Validation**: Strict type checking prevents injection attacks
4. **Authentication**: Box JWT authentication with enterprise-level permissions
5. **Audit Trail**: Comprehensive logging of all extraction and application operations

### Address Validation & Mismatch Detection

The system includes sophisticated address validation capabilities:

1. **Extraction**: AI extracts addresses from financial documents
2. **Validation**: Compares extracted addresses against client records
3. **Mismatch Detection**: Identifies discrepancies and flags for review
4. **Bulk Resolution**: Allows group updates when address changes are confirmed

### Future Enhancements

1. **Machine Learning Improvements**: Enhanced document type classification
2. **Custom Field Templates**: Dynamic template creation for specialized documents
3. **Confidence Scoring**: AI confidence metrics for extraction quality assessment
4. **Bulk Template Management**: Administrative tools for template lifecycle management
5. **Real-time Processing**: WebSocket-based real-time extraction status updates

---

## Conclusion

This metadata extraction and application system provides a robust, scalable solution for automated document processing. The combination of Box AI's advanced extraction capabilities with structured enterprise metadata templates ensures high accuracy while maintaining flexibility for various document types.

The progressive enhancement approach, comprehensive error handling, and parallel processing capabilities make this system suitable for production financial document processing at scale.

Key benefits:
- **High Accuracy**: AI-powered extraction with multiple fallback mechanisms
- **Type Safety**: Strict validation and sanitization before data persistence
- **Scalability**: Parallel processing with configurable worker pools
- **Flexibility**: Support for multiple document types and custom templates
- **Audit Trail**: Comprehensive logging for compliance and debugging
- **Address Validation**: Automated address verification and mismatch detection 