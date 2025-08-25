/**
 * Document Processing Functions
 * Handles Box document uploads and metadata processing
 */

// Track document counts by type
window.documentCounts = {};

// Track processed files to prevent double-counting - using localStorage for persistence
const processedFiles = (() => {
    // Try to load previously processed files from localStorage
    try {
        const savedProcessed = localStorage.getItem('processedFiles');
        return savedProcessed ? new Map(JSON.parse(savedProcessed)) : new Map();
    } catch (e) {
        console.error('Error loading processed files from localStorage:', e);
        return new Map();
    }
})();

// Helper function to save processed files to localStorage
function saveProcessedFiles() {
    try {
        localStorage.setItem('processedFiles', JSON.stringify(Array.from(processedFiles.entries())));
    } catch (e) {
        console.error('Error saving processed files to localStorage:', e);
    }
}

/**
 * Show error message in the UI
 * @param {string} message - Error message to display
 */
function showErrorMessage(message) {
    const uploaderElement = document.getElementById('box-uploader');
    if (uploaderElement) {
        uploaderElement.innerHTML = `
            <div class="flex items-center justify-center h-full p-6 text-center">
                <div>
                    <div class="text-red-500 mb-4">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                    </div>
                    <h3 class="text-lg font-semibold mb-2">Upload Error</h3>
                    <p class="text-gray-600">${message}</p>
                    <button onclick="window.location.reload()" class="mt-4 bg-horizon-primary text-white py-2 px-4 rounded hover:bg-horizon-secondary">
                        Try Again
                    </button>
                </div>
            </div>
        `;
    }
}

/**
 * Get the CSRF token from cookies
 * @returns {string} - CSRF token value
 */
function getCSRFToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Update document card based on document type
 * @param {string} documentType - The type of document identified
 */
function updateDocumentCard(documentType) {
    if (!documentType) {
        console.warn("Cannot update document card: No document type provided");
        return;
    }
    
    // Log the document type for debugging
    console.log(`Updating document card for type: ${documentType}`);
    
    // Map specific document types to their card names if they don't match exactly
    let mappedDocType = documentType;
    
    // Create mappings for common document type variations
    const typeMap = {
        'Personal Financial Statement': 'Personal Financial Statement',
        'Financial Statement': 'Personal Financial Statement',
        'PFS': 'Personal Financial Statement',
        'W-2': 'W-2',
        'W2': 'W-2',
        'Form W-2': 'W-2',
        'Account Statement': 'Account Statement',
        'Bank Statement': 'Account Statement',
        'Brokerage Statement': 'Account Statement',
        'Mortgage Statement': 'Mortgage Statement',
        'Trust Document': 'Trust Document',
        'Asset List': 'Asset List',
        '1040': '1040',
        'Form 1040': '1040',
        '1099': '1099',
        'Form 1099': '1099',
        'Life Insurance Document': 'Life Insurance Document',
        'Insurance Policy': 'Life Insurance Document',
        'Other': 'Other'
    };
    
    // Check if we have a mapping for this document type
    if (typeMap[documentType]) {
        mappedDocType = typeMap[documentType];
        console.log(`Mapped document type ${documentType} to ${mappedDocType}`);
    } else {
        // If no mapping found, default to "Other"
        mappedDocType = "Other";
        console.log(`No mapping found for ${documentType}, defaulting to "Other" category`);
    }
    
    // Increment the count for this document type
    window.documentCounts[mappedDocType] = (window.documentCounts[mappedDocType] || 0) + 1;
    console.log(`New count for ${mappedDocType}: ${window.documentCounts[mappedDocType]}`);
    
    // Find all cards with this document type
    const cards = document.querySelectorAll(`[data-document-type="${mappedDocType}"]`);
    console.log(`Found ${cards.length} cards for document type "${mappedDocType}"`);
    
    if (cards.length > 0) {
        cards.forEach(card => {
            // Add the uploaded class
            card.classList.add('document-card-uploaded');
            console.log(`Added 'document-card-uploaded' class to card for ${mappedDocType}`);
            
            // Update the count
            const countElement = card.querySelector('.document-count');
            if (countElement) {
                countElement.textContent = window.documentCounts[mappedDocType];
                console.log(`Updated count for ${mappedDocType} to ${window.documentCounts[mappedDocType]}`);
            } else {
                console.warn(`Count element not found in card for ${mappedDocType}`);
            }
        });
    } else {
        console.warn(`No card found for document type: ${mappedDocType}`);
        console.log(`All available cards:`, 
            Array.from(document.querySelectorAll('[data-document-type]'))
                .map(el => `${el.getAttribute('data-document-type')} (id: ${el.id})`));
        
        // Try to match to specific document types first
        if (documentType.includes('1099')) {
            console.log(`Matching ${documentType} to general 1099 card`);
            updateDocumentCard('1099');
        } else if (documentType.includes('W-2') || documentType.includes('W2')) {
            console.log(`Matching ${documentType} to general W-2 card`);
            updateDocumentCard('W-2');
        } else if (documentType.includes('1040')) {
            console.log(`Matching ${documentType} to general 1040 card`);
            updateDocumentCard('1040');
        } else if (documentType.includes('Account') || documentType.includes('Statement')) {
            console.log(`Matching ${documentType} to Account Statement card`);
            updateDocumentCard('Account Statement');
        } else if (documentType.includes('Insurance')) {
            console.log(`Matching ${documentType} to Life Insurance Document card`);
            updateDocumentCard('Life Insurance Document');
        } else if (documentType.includes('Financial') || documentType.includes('Personal Financial')) {
            console.log(`Matching ${documentType} to Personal Financial Statement card`);
            updateDocumentCard('Personal Financial Statement');
        } else {
            // If no specific match is found, default to "Other" category
            console.log(`No specific match found for ${documentType}, using "Other" category`);
            updateDocumentCard('Other');
        }
    }
}

/**
 * Process a file with metadata extraction
 * @param {Object} file - File information object
 * @returns {Promise<Object>} - Processing result
 */
async function processFileWithMetadata(file) {
    try {
        // Check if file has already been processed to prevent double-counting
        const fileKey = file.fileId;
        if (processedFiles.has(fileKey) && processedFiles.get(fileKey).processingComplete) { // Check if already fully processed
            console.log(`File ${file.fileId} (${file.fileName}) has already been processed. Skipping.`);
            const indicator = document.getElementById(`processing-indicator-${file.fileId}`);
            if (indicator) indicator.remove();
            return processedFiles.get(fileKey);
        }
        
        console.log(`========== LIGHTWEIGHT PROCESSING FOR FILE ${file.fileId} (${file.fileName}) ==========`);

        // Mark as in-progress
        processedFiles.set(fileKey, {
            fileName: file.fileName,
            fileId: file.fileId,
            success: false, // Default to false until confirmed
            message: 'Initial processing in progress',
            documentType: null,
            inProgress: true,
            processingComplete: false // Mark as not fully processed yet
        });
        saveProcessedFiles();
        
        // Step 1: Ensure the base template is attached (lightweight call)
        console.log(`Ensuring base metadata template for file ID ${file.fileId}...`);
        let templateEnsured = false;
        try {
            const templateResponse = await fetch(`/api/box/ensure-template/?fileId=${file.fileId}&template=financialDocumentBase&scope=enterprise_218068865`);
            if (templateResponse.ok) {
                const templateResult = await templateResponse.json();
                console.log(`Template attachment result for ${file.fileName}:`, templateResult);
                templateEnsured = templateResult.success;
            } else {
                const errorText = await templateResponse.text();
                console.error(`Failed to ensure template for file ID ${file.fileId}: ${errorText}`);
            }
        } catch (e) {
            console.error(`Error ensuring template for file ID ${file.fileId}:`, e);
        }

        // Step 2: Client-side document type guessing from filename for quick UI update
        let identifiedType = null;
        const fileNameLower = file.fileName.toLowerCase();
        if (fileNameLower.includes('1099')) identifiedType = '1099';
        else if (fileNameLower.includes('w-2') || fileNameLower.includes('w2')) identifiedType = 'W-2';
        else if (fileNameLower.includes('statement') && (fileNameLower.includes('account') || fileNameLower.includes('bank'))) identifiedType = 'Account Statement';
        else if (fileNameLower.includes('mortgage')) identifiedType = 'Mortgage Statement';
        else if (fileNameLower.includes('1040')) identifiedType = '1040';
        // Add more client-side guesses if needed

        if (identifiedType) {
            console.log(`UPDATING CARD (Client-side guess): Document type inferred from filename for file ID ${file.fileId}: ${identifiedType}`);
            updateDocumentCard(identifiedType); // Update card based on guess
        }

        // Remove processing indicator as this lightweight process is done.
        // The batch process will handle its own indicators if needed or a global one.
        const indicator = document.getElementById(`processing-indicator-${file.fileId}`);
        if (indicator) indicator.remove();

        const result = {
            fileName: file.fileName,
            fileId: file.fileId,
            success: templateEnsured, // Success based on template ensuring for now
            message: templateEnsured ? 'Initial processing complete, template ensured.' : 'Initial processing complete, template ensure failed.',
            documentType: identifiedType, // Store guessed type
            inProgress: false, // No longer in individual progress
            processingComplete: false // Mark as NOT YET FULLY PROCESSED by AI
        };

        processedFiles.set(fileKey, result);
        saveProcessedFiles();
        
        console.log(`========== LIGHTWEIGHT PROCESSING COMPLETE FOR FILE ${file.fileId} (${file.fileName}) ==========`);
        return result;

    } catch (error) {
        console.error(`Error in lightweight processing for ${file.fileName} (ID: ${file.fileId}):`, error);
        const errorResult = {
            fileName: file.fileName,
            fileId: file.fileId,
            success: false,
            message: `Lightweight processing error: ${error.message}`,
            documentType: null,
            inProgress: false,
            processingComplete: false
        };
        processedFiles.set(file.fileId, errorResult);
        saveProcessedFiles();
        const indicator = document.getElementById(`processing-indicator-${file.fileId}`);
        if (indicator) indicator.remove(); // Remove indicator on error too
        return errorResult;
    }
}

/**
 * Extract metadata using Box AI API
 * @param {string} fileId - Box file ID
 * @param {string} templateKey - The metadata template key to use
 * @returns {Promise<Object>} - Response with extraction result
 */
async function extractMetadataWithBoxAI(fileId, templateKey = 'financialDocumentBase') {
    try {
        console.log(`========== STARTING IMPROVED BOX AI EXTRACTION FOR FILE ID: ${fileId} ==========`);
        console.log(`Using template key: ${templateKey}`);
        
        // Define the request payload according to Box AI API requirements
        let requestData;
        
        if (templateKey === 'financialDocumentBase') {
            // Use custom Financial Document Classifier agent for document type identification
            requestData = {
                mode: "single_item_qa",
                prompt: `Analyze this financial document and classify it. Respond ONLY with valid JSON in this exact format:
{
  "documentType": "[exact type from list]",
  "confidence": [0.0 to 1.0],
  "isLegible": [true/false],
  "issuerName": "[company name if identifiable or empty string]",
  "recipientName": "[recipient name if identifiable or empty string]"
}

Valid documentType values (use exact text):
- "1099" - IRS Form 1099 (any variant)
- "W-2" - IRS Form W-2 
- "Account Statement" - Bank/brokerage/retirement statements
- "Mortgage Statement" - Mortgage/loan statements
- "Trust Document" - Trust agreements or related documents
- "Asset List" - Investment holdings or asset summaries
- "1040" - IRS Form 1040
- "Personal Financial Statement" - Net worth or financial summaries
- "Life Insurance Document" - Insurance policies or forms
- "Other" - Financial documents not matching above categories`,
                items: [{
                    id: fileId,
                    type: "file"
                }],
                ai_agent: {
                    id: "36769377",
                    type: "ai_agent_id"
                }
            };
        } else {
            // Use generic structured extraction for other templates
            requestData = {
            metadata_template: {
                template_key: templateKey,
                type: "metadata_template",
                    scope: "enterprise_218068865"
            },
            items: [{
                id: fileId,
                type: "file"
            }],
            ai_agent: {
                type: "ai_agent_extract_structured",
                long_text: {
                    model: "azure__openai__gpt_4o_mini"
                },
                basic_text: {
                    model: "azure__openai__gpt_4o_mini"
                }
            }
        };
        }
        
        console.log(`Sending Box AI extraction request with payload:`, requestData);
        
        // Use fetch API to call our backend, which will forward the request to Box API
        const response = await fetch('/api/box/process-document/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                fileId: fileId,
                templateKey: templateKey,
                requestData: requestData
            })
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Box AI API returned error: ${response.status} - ${errorText}`);
        }
        
        const result = await response.json();
        console.log(`Box AI extraction response:`, result);
        
        // Extract the data from the result based on its structure
        let extractedData = {};
        
        if (result.baseMetadataResult && result.baseMetadataResult.data) {
            // Use data from baseMetadataResult if available
            console.log("Using data from baseMetadataResult");
            extractedData = result.baseMetadataResult.data;
        } else if (result.data) {
            // Use direct data field if available
            console.log("Using direct data field");
            extractedData = result.data;
        } else if (result.fields && Array.isArray(result.fields)) {
            // Handle structured fields format
            console.log("Processing structured fields format");
            extractedData = {};
            for (const field of result.fields) {
                if (field.key && 'value' in field) {
                    extractedData[field.key] = field.value;
                }
            }
        } else if (result.answer) {
            // Handle answer field if present (most common from Box AI)
            console.log("Processing answer field");
            if (typeof result.answer === 'object') {
                extractedData = result.answer;
            } else if (typeof result.answer === 'string') {
                try {
                    // Try to parse as JSON
                    const parsed = JSON.parse(result.answer);
                    if (typeof parsed === 'object') {
                        extractedData = parsed;
                    } else {
                        extractedData = { extracted_text: result.answer };
                    }
                } catch (e) {
                    // Not valid JSON, use as text
                    extractedData = { extracted_text: result.answer };
                }
            }
        } else {
            // If none of the above, extract all relevant properties from the result
            console.log("Extracting relevant properties from result");
            const excludedFields = ['ai_agent_info', 'completion_reason', 'created_at', 'success', 'message', 'fileId'];
            extractedData = Object.fromEntries(
                Object.entries(result).filter(([key]) => 
                    !excludedFields.includes(key) && !key.startsWith('$')
                )
            );
        }
        
        // Make sure we have a documentType field
        if (extractedData && extractedData.documentType) {
            console.log(`Extracted document type: ${extractedData.documentType}`);
        } else {
            console.warn("No document type found in extracted data");
        }
        
        console.log("Extracted data:", extractedData);
        
        return {
            success: true,
            data: extractedData,
            message: 'Metadata extraction completed successfully with AI',
            fileId: fileId
        };
    } catch (error) {
        console.error(`Error in improved Box AI extraction for file ID ${fileId}:`, error);
        return {
            success: false,
            message: `AI extraction error: ${error.message}`,
            fileId: fileId
        };
    }
}

// Function to initialize Box Content uploader for document upload page
async function initializeBoxContentUploader(clientName, logoUrl) {
    try {
        console.log("========== INITIALIZING BOX CONTENT UPLOADER FOR DOCUMENT UPLOAD ==========");
        
        // Step 1: Get or create the client folder and access the "Shared with Advisor" subfolder
        console.log(`Getting client folder for: ${clientName}`);
        const folderResponse = await fetch('/api/box/client-folder/');
        if (!folderResponse.ok) {
            const errorText = await folderResponse.text();
            console.error(`Failed to get client folder: ${errorText}`);
            throw new Error('Failed to get client folder');
        }
        const folderData = await folderResponse.json();
        const clientFolderId = folderData.folderId;
        console.log(`Client folder retrieved, ID: ${clientFolderId} for client: ${folderData.clientName}`);
        
        // Step 1.5: Get the "Shared with Advisor" subfolder for document uploads
        console.log(`Looking for "Shared with Advisor" subfolder in client folder ${clientFolderId}`);
        let sharedFolderId = null;
        try {
            // Get items in the client folder to find the "Shared with Advisor" subfolder
            const subfolderResponse = await fetch(`/api/box/check-uploads/?folderId=${clientFolderId}`);
            if (subfolderResponse.ok) {
                const subfolderData = await subfolderResponse.json();
                console.log(`Client folder contents:`, subfolderData);
                
                // Look for "Shared with Advisor" folder
                const sharedFolder = subfolderData.files?.find(item => 
                    item.type === 'folder' && item.name === 'Shared with Advisor'
                );
                
                if (sharedFolder) {
                    sharedFolderId = sharedFolder.id;
                    console.log(`Found "Shared with Advisor" subfolder: ${sharedFolderId}`);
                } else {
                    console.warn(`"Shared with Advisor" subfolder not found, using client folder directly`);
                    sharedFolderId = clientFolderId;
                }
            } else {
                console.warn(`Could not check client folder contents, using client folder directly`);
                sharedFolderId = clientFolderId;
            }
        } catch (error) {
            console.warn(`Error finding "Shared with Advisor" subfolder: ${error.message}, using client folder directly`);
            sharedFolderId = clientFolderId;
        }
        
        const folderId = sharedFolderId;
        console.log(`Using folder ID for uploads: ${folderId}`);
        
        // Check for existing files in the folder
        await checkUploadedFiles(folderId);
        
        // Step 2: Get a downscoped token for this folder
        console.log(`Fetching downscoped token for folder ID: ${folderId}`);
        const tokenResponse = await fetch(`/api/box/explorer-token/?folderId=${folderId}`);
        if (!tokenResponse.ok) {
            const errorText = await tokenResponse.text();
            console.error(`Failed to get token: ${errorText}`);
            throw new Error('Failed to get token');
        }
        const tokenData = await tokenResponse.json();
        const accessToken = tokenData.token;
        console.log(`Token retrieved successfully, length: ${accessToken.length} chars`);
        
        // Step 3: Initialize the Box Content Uploader
        if (typeof Box !== 'undefined' && Box.ContentUploader) {
            console.log("Box SDK loaded, initializing ContentUploader for document upload");
            const contentUploader = new Box.ContentUploader();
            
            // Store folder ID in the uploader element for easier access later
            const uploaderElement = document.getElementById('box-uploader');
            if (uploaderElement) {
                uploaderElement.dataset.folderId = folderId;
                console.log(`Set folder ID ${folderId} in uploader element's dataset`);
            }
            
            // Track uploaded files to process metadata
            const uploadedFiles = [];
            
            // Keep track of files currently being processed to avoid duplicate processing
            const processingQueue = new Set();
            
            // Set up event handlers
            console.log("Setting up Box uploader event listeners for document upload");
            
            contentUploader.addListener('upload', function(e) {
                console.log('Document upload event:', e);
                
                // Check if this is a file object with complete data
                if (e.type === 'file' && e.id) {
                    console.log(`========== DOCUMENT UPLOAD EVENT FOR FILE ==========`);
                    console.log(`File: ${e.name} (ID: ${e.id})`);
                    
                    // Add to current session tracking
                    addToCurrentSession({
                        id: e.id,
                        name: e.name,
                        size: e.size,
                        created_at: new Date().toISOString(),
                        metadata: {}
                    });
                    
                    // Check if this file has been processed or is being processed
                    if (processedFiles.has(e.id) || processingQueue.has(e.id)) {
                        console.log(`File ${e.id} already processed or in processing queue. Skipping.`);
                        return;
                    }
                    
                    // Store uploaded file info for metadata processing
                    if (!uploadedFiles.some(f => f.fileId === e.id)) {
                        uploadedFiles.push({
                            fileId: e.id,
                            fileName: e.name
                        });
                        console.log(`Added file to processing queue, total files: ${uploadedFiles.length}`);
                    }
                    
                } else if (e.event === 'complete') {
                    console.log(`========== DOCUMENT UPLOAD COMPLETE ==========`);
                    console.log(`File: ${e.file?.name} (ID: ${e.file?.id})`);
                    
                    // Check if we have a valid file ID
                    if (e.file && e.file.id) {
                        console.log(`SUCCESS: Document upload complete for file ID ${e.file.id}: ${e.file.name}`);
                        
                        // Only add to queue if not already processed or in processing queue
                        if (!processedFiles.has(e.file.id) && !processingQueue.has(e.file.id)) {
                            // Add to processing queue to prevent duplicate processing
                            processingQueue.add(e.file.id);
                            
                            // Process the file with a delay
                            setTimeout(async () => {
                                try {
                                    console.log(`Starting processing for uploaded file: ${e.file.name} (ID: ${e.file.id})`);
                                    
                                    // Process only if not already processed during that delay
                                    if (!processedFiles.has(e.file.id)) {
                                        const result = await processFileWithMetadata({
                                            fileId: e.file.id,
                                            fileName: e.file.name
                                        });
                                        console.log(`Processing result:`, result);
                                    } else {
                                        console.log(`File ${e.file.id} was processed during the delay. Skipping.`);
                                    }
                                    
                                    // Remove from processing queue
                                    processingQueue.delete(e.file.id);
                                    
                                    // Refresh the file list to show updated metadata
                                    await checkUploadedFiles(folderId);
                                    
                                } catch (error) {
                                    console.error(`Error in processing: ${error}`);
                                    processingQueue.delete(e.file.id);
                                }
                            }, 2000); // 2 seconds delay
                        }
                    }
                }
            });
            
            contentUploader.addListener('complete', async function(e) {
                console.log('All document uploads completed:', e);
                
                if (uploadedFiles.length === 0) {
                    console.warn("No files in upload queue to process");
                    return;
                }
                
                // Filter out already processed files to avoid double processing
                const pendingFiles = uploadedFiles.filter(file => 
                    !processedFiles.has(file.fileId) && !processingQueue.has(file.fileId)
                );
                
                console.log(`Found ${pendingFiles.length} files that still need processing out of ${uploadedFiles.length} total files`);
                
                // If all files are already processed, just refresh the file list
                if (pendingFiles.length === 0) {
                    console.log('All files have already been processed');
                    await checkUploadedFiles(folderId);
                    return;
                }
                
                // Extract file IDs for processing
                const fileIds = pendingFiles.map(file => file.fileId);
                
                // Use the startDocumentProcessing function from the document upload page
                if (typeof startDocumentProcessing === 'function') {
                    console.log(`Starting document processing for ${fileIds.length} files using startDocumentProcessing function`);
                    await startDocumentProcessing(fileIds);
                } else {
                    console.log('startDocumentProcessing function not available, processing individually');
                    // Process files individually
                    for (const file of pendingFiles) {
                        if (!processingQueue.has(file.fileId)) {
                            processingQueue.add(file.fileId);
                            try {
                                await processFileWithMetadata(file);
                            } finally {
                                processingQueue.delete(file.fileId);
                            }
                        }
                    }
                }
                
                // Refresh the file list after processing
                await checkUploadedFiles(folderId);
            });
            
            console.log(`Showing Box uploader for document upload with folder ID: ${folderId}`);
            contentUploader.show(folderId, accessToken, {
                container: '#box-uploader',
                fileLimit: 100,
                canUpload: true,
                canSetShareAccess: false,
                logoUrl: logoUrl
            });
            
            console.log('Box Content Uploader initialized successfully for document upload');
        } else {
            console.error("Box SDK not available:", { 
                boxDefined: typeof Box !== 'undefined',
                uploaderAvailable: typeof Box !== 'undefined' && !!Box.ContentUploader
            });
            showErrorMessage("Document uploader failed to initialize");
        }
    } catch (error) {
        console.error("Error setting up Box uploader for document upload:", error);
        showErrorMessage(error.message || "Failed to set up document uploader");
    }
}

// Function to initialize Box Content uploader (original for Documents tab)
async function initializeBoxContent(username, logoUrl) {
    try {
        console.log("========== INITIALIZING BOX CONTENT UPLOADER ==========");
        
        // Get or create the onboarding subfolder for this client
        console.log(`Fetching onboarding folder for user: ${username}`);
        const folderResponse = await fetch(`/api/box/onboarding-folder/?clientName=${encodeURIComponent(username)}`);
        if (!folderResponse.ok) {
            const errorText = await folderResponse.text();
            console.error(`Failed to get onboarding folder: ${errorText}`);
            throw new Error('Failed to get onboarding folder');
        }
        const folderData = await folderResponse.json();
        const folderId = folderData.folderId;
        console.log(`Onboarding folder retrieved, ID: ${folderId}`);
        
        // Check for existing files in the folder
        await checkUploadedFiles(folderId);
        
        // Then, get a downscoped token for this folder
        console.log(`Fetching downscoped token for folder ID: ${folderId}`);
        const tokenResponse = await fetch(`/api/box/explorer-token/?folderId=${folderId}`);
        if (!tokenResponse.ok) {
            const errorText = await tokenResponse.text();
            console.error(`Failed to get token: ${errorText}`);
            throw new Error('Failed to get token');
        }
        const tokenData = await tokenResponse.json();
        const accessToken = tokenData.token;
        console.log(`Token retrieved successfully, length: ${accessToken.length} chars`);
        
        // Initialize the Box Content Uploader with the folder ID and token
        if (typeof Box !== 'undefined' && Box.ContentUploader) {
            console.log("Box SDK loaded, initializing ContentUploader");
            const contentUploader = new Box.ContentUploader();
            
            // Store folder ID in the uploader element for easier access later
            const uploaderElement = document.getElementById('box-uploader');
            if (uploaderElement) {
                uploaderElement.dataset.folderId = folderId;
                console.log(`Set folder ID ${folderId} in uploader element's dataset`);
            }
            
            // Track uploaded files to process metadata
            const uploadedFiles = [];
            
            // Keep track of files currently being processed to avoid duplicate processing
            const processingQueue = new Set();
            
            // Set up event handlers
            console.log("Setting up Box uploader event listeners");
            
            contentUploader.addListener('select', function(e) {
                console.log('Files selected for upload:', e);
            });
            
            contentUploader.addListener('upload', function(e) {
                console.log('Upload event:', e.event, e);
                
                // Check if this is a file object with complete data
                if (e.type === 'file' && e.id) {
                    console.log(`========== UPLOAD EVENT FOR FILE ==========`);
                    console.log(`File: ${e.name} (ID: ${e.id})`);
                    console.log(`File details:`, JSON.stringify(e, null, 2));
                    
                    // Add to current session tracking
                    addToCurrentSession({
                        id: e.id,
                        name: e.name,
                        size: e.size,
                        created_at: new Date().toISOString(),
                        metadata: {}
                    });
                    
                    // Check if this file has been processed or is being processed
                    if (processedFiles.has(e.id) || processingQueue.has(e.id)) {
                        console.log(`File ${e.id} already processed or in processing queue. Skipping.`);
                        return;
                    }
                    
                    // Store uploaded file info for metadata processing if it's not already being tracked
                    if (!uploadedFiles.some(f => f.fileId === e.id)) {
                        uploadedFiles.push({
                            fileId: e.id,
                            fileName: e.name
                        });
                        console.log(`Added file to processing queue, total files: ${uploadedFiles.length}`);
                    }
                    
                    // Show processing indicator
                    const processingDiv = document.createElement('div');
                    processingDiv.className = 'mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-md';
                    processingDiv.id = `processing-indicator-${e.id}`;
                    processingDiv.innerHTML = `
                        <div class="flex items-center">
                            <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-horizon-primary" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            <span>Processing document: ${e.name}...</span>
                        </div>
                    `;
                    
                    // Insert the processing indicator after the uploader
                    const uploaderElement = document.getElementById('box-uploader');
                    if (uploaderElement && !document.getElementById(`processing-indicator-${e.id}`)) {
                        uploaderElement.insertAdjacentElement('afterend', processingDiv);
                    }
                    
                } else if (e.event === 'complete') {
                    console.log(`========== UPLOAD COMPLETE ==========`);
                    console.log(`File: ${e.file?.name} (ID: ${e.file?.id})`);
                    
                    // Check if we have a valid file ID
                    if (e.file && e.file.id) {
                        console.log(`SUCCESS: Upload complete for file ID ${e.file.id} from Box for file: ${e.file.name}`);
                        
                        // Only add to queue if not already processed or in processing queue
                        if (!processedFiles.has(e.file.id) && !processingQueue.has(e.file.id)) {
                            // Add to processing queue to prevent duplicate processing
                            processingQueue.add(e.file.id);
                            
                            // Process the file with a delay
                            setTimeout(async () => {
                                try {
                                    console.log(`Starting delayed processing for file: ${e.file.name} (ID: ${e.file.id})`);
                                    
                                    // Process only if not already processed during that delay
                                    if (!processedFiles.has(e.file.id)) {
                                        const result = await processFileWithMetadata({
                                            fileId: e.file.id,
                                            fileName: e.file.name
                                        });
                                        console.log(`Delayed processing result:`, result);
                                    } else {
                                        console.log(`File ${e.file.id} was processed during the delay. Skipping.`);
                                    }
                                    
                                    // Remove from processing queue
                                    processingQueue.delete(e.file.id);
                                    
                                    // Refresh the file list to show updated metadata
                                    await checkUploadedFiles(folderId);
                                    
                                } catch (error) {
                                    console.error(`Error in delayed processing: ${error}`);
                                    processingQueue.delete(e.file.id);
                                }
                            }, 3000); // 3 seconds for good measure
                        } else {
                            console.log(`File ${e.file.id} already processed or in processing queue. Skipping.`);
                        }
                    }
                } else if (e.event === 'progress') {
                    console.log(`Upload progress for ${e.file?.name || 'unknown file'}: ${e.progress}%`);
                } else if (e.event === 'error') {
                    console.error(`Upload error for ${e.file?.name || 'unknown file'}:`, e.error);
                }
            });
            
            contentUploader.addListener('complete', async function(e) {
                console.log('All uploads completed:', e);
                console.log(`Checking ${uploadedFiles.length} uploaded files for metadata extraction`);
                
                // Hide individual processing indicators
                uploadedFiles.forEach(file => {
                    const indicator = document.getElementById(`processing-indicator-${file.fileId}`);
                    if (indicator) {
                        console.log(`Removing processing indicator for file ${file.fileId}`);
                        indicator.remove();
                    }
                });
                
                if (uploadedFiles.length === 0) {
                    console.warn("No files in upload queue to process");
                    return;
                }
                
                // Filter out already processed files to avoid double processing
                const pendingFiles = uploadedFiles.filter(file => 
                    !processedFiles.has(file.fileId) && !processingQueue.has(file.fileId)
                );
                
                console.log(`Found ${pendingFiles.length} files that still need processing out of ${uploadedFiles.length} total files`);
                
                // If all files are already processed, just refresh the file list
                if (pendingFiles.length === 0) {
                    console.log('All files have already been processed');
                    await checkUploadedFiles(folderId);
                    return;
                }
                
                // Extract file IDs for processing
                const fileIds = pendingFiles.map(file => file.fileId);
                
                // Use our new startDocumentProcessing function from the document upload page
                if (typeof startDocumentProcessing === 'function') {
                    console.log(`Starting document processing for ${fileIds.length} files using startDocumentProcessing function`);
                    await startDocumentProcessing(fileIds);
                } else {
                    console.error('startDocumentProcessing function not available, falling back to old batch processing');
                    
                    // Fallback to the old processing logic if the function isn't available
                    try {
                        // Mark files as being processed
                        pendingFiles.forEach(file => {
                            processingQueue.add(file.fileId);
                        });
                        
                        // Process all files in a single batch request
                        const batchResult = await processBatchFilesWithMetadata(pendingFiles);
                        
                        // Remove all files from processing queue
                        pendingFiles.forEach(file => {
                            processingQueue.delete(file.fileId);
                        });
                        
                        if (batchResult.success) {
                            console.log(`Successfully processed ${batchResult.results.length} files in parallel`);
                        } else {
                            console.error(`Batch processing failed: ${batchResult.message}`);
                        }
                    } catch (error) {
                        console.error(`Error in fallback batch processing:`, error);
                        // Remove files from processing queue on error
                        pendingFiles.forEach(file => {
                            processingQueue.delete(file.fileId);
                        });
                    }
                }
                
                // Refresh the file list after processing
                await checkUploadedFiles(folderId);
            });
            
            console.log(`Showing Box uploader with folder ID: ${folderId}`);
            contentUploader.show(folderId, accessToken, {
                container: '#box-uploader',
                fileLimit: 100,
                canUpload: true,
                canSetShareAccess: false,
                logoUrl: logoUrl
            });
            
            console.log('Box Content Uploader initialized successfully');
        } else {
            console.error("Box SDK not available:", { 
                boxDefined: typeof Box !== 'undefined',
                uploaderAvailable: typeof Box !== 'undefined' && !!Box.ContentUploader
            });
            showErrorMessage("Document uploader failed to initialize");
        }
    } catch (error) {
        console.error("Error setting up Box uploader:", error);
        showErrorMessage(error.message || "Failed to set up document uploader");
    }
}

/**
 * Check for uploaded files in a folder
 * @param {string} folderId - The Box folder ID
 * @returns {Promise<Object>} - Result containing files in the folder
 */
async function checkUploadedFiles(folderId) {
    try {
        console.log(`Checking for uploaded files in folder ${folderId}...`);
        const response = await fetch(`/api/box/check-uploads/?folderId=${folderId}`);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error(`Failed to check uploads: ${errorText}`);
            throw new Error(`Failed to check uploads: ${errorText}`);
        }
        
        const result = await response.json();
        console.log(`Found ${result.files.length} files in folder ${folderId}:`, result.files);
        
        // Remove the old diagnostic div if it exists
        const existingDiagnostic = document.getElementById('upload-diagnostic');
        if (existingDiagnostic) {
            existingDiagnostic.remove();
        }
        
        // Display uploaded files in the UI
        if (result.files && result.files.length > 0) {
            displayUploadedFiles(result.files);
        }
        
        return result;
    } catch (error) {
        console.error(`Error checking uploaded files: ${error}`);
        return {
            success: false,
            message: error.message || 'Error checking uploaded files',
            files: []
        };
    }
}

// Track files uploaded in current session only
let currentSessionFiles = new Map(); // fileId -> file object

/**
 * Add a file to current session tracking
 * @param {Object} file - File object
 */
function addToCurrentSession(file) {
    currentSessionFiles.set(file.id, file);
    displayCurrentSessionFiles();
}

/**
 * Update a file's metadata in current session tracking
 * @param {string} fileId - File ID
 * @param {Object} metadata - Updated metadata
 */
function updateCurrentSessionFile(fileId, metadata) {
    if (currentSessionFiles.has(fileId)) {
        const file = currentSessionFiles.get(fileId);
        file.metadata = { ...file.metadata, ...metadata };
        currentSessionFiles.set(fileId, file);
        displayCurrentSessionFiles();
    }
}

/**
 * Display only files uploaded in current session
 */
function displayCurrentSessionFiles() {
    const filesContainer = document.getElementById('uploaded-files-container');
    const filesList = document.getElementById('uploaded-files-list');
    
    if (!filesContainer || !filesList) {
        console.error('Could not find uploaded files container elements');
        return;
    }
    
    const files = Array.from(currentSessionFiles.values());
    
    if (files.length === 0) {
        filesContainer.classList.add('hidden');
        return;
    }
    
    // Sort files by upload time (newest first)
    const sortedFiles = [...files].sort((a, b) => {
        return new Date(b.created_at || b.modified_at || 0) - new Date(a.created_at || a.modified_at || 0);
    });
    
    // Clear the list
    filesList.innerHTML = '';
    
    // Add each file to the list
    sortedFiles.forEach(file => {
        const documentType = file.metadata?.type || 'Unknown';
        const fileSize = formatFileSize(file.size || 0);
        const uploadTime = new Date(file.created_at || file.modified_at || Date.now()).toLocaleTimeString();
        const processingStatus = processedFiles.has(file.id) ? 'Processed' : 'Pending';
        const statusColorClass = processedFiles.has(file.id) ? 'text-green-500' : 'text-yellow-500';
        
        const fileItem = document.createElement('li');
        fileItem.className = 'py-3 first:pt-0 last:pb-0';
        fileItem.innerHTML = `
            <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium text-gray-900 truncate">${file.name}</p>
                    <div class="flex flex-wrap gap-2 mt-1">
                        <p class="text-xs text-gray-500">Uploaded: ${uploadTime}</p>
                        ${documentType !== 'Unknown' ? `<p class="text-xs font-medium text-horizon-primary">${documentType}</p>` : ''}
                    </div>
                </div>
                <div>
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColorClass} bg-${statusColorClass.replace('text', 'bg')}-50">
                        ${processingStatus}
                    </span>
                </div>
            </div>
        `;
        
        filesList.appendChild(fileItem);
    });
    
    // Show the container
        filesContainer.classList.remove('hidden');
    }

/**
 * Legacy display function - now redirects to session-based display
 * @param {Array} files - Array of file objects (ignored, we use current session tracking)
 */
function displayUploadedFiles(files) {
    // Just display current session files instead of all files from folder
    displayCurrentSessionFiles();
}

/**
 * Get metadata for a specific file
 * @param {string} fileId - The Box file ID
 * @returns {Promise<Object>} - The file metadata
 */
async function getFileMetadata(fileId) {
    try {
        console.log(`Fetching metadata for file ${fileId}...`);
        
        // First try the original URL
        let url = `/api/box/get-metadata/?fileId=${fileId}&template=financialDocumentBase&scope=enterprise_218068865`;
        console.log(`Trying API URL: ${url}`);
        
        let response;
        try {
            response = await fetch(url);
            if (response.ok) {
                const result = await response.json();
                console.log(`Metadata result for file ${fileId}:`, result);
                return result;
            }
            console.warn(`First URL attempt failed with status: ${response.status}`);
        } catch (error) {
            console.warn(`Error with first URL attempt: ${error.message}`);
        }
        
        // If original URL failed, try the test URL
        url = `/api/box/test-metadata/?fileId=${fileId}&template=financialDocumentBase&scope=enterprise_218068865`;
        console.log(`Trying alternate API URL: ${url}`);
        
        try {
            response = await fetch(url);
            if (response.ok) {
                const result = await response.json();
                console.log(`Metadata result for file ${fileId} (from test URL):`, result);
                return result;
            }
            
            // If 404, the metadata doesn't exist yet
            if (response.status === 404) {
                console.log(`No metadata found for file ${fileId}`);
                return { success: false, message: 'No metadata found' };
            }
            
            const errorText = await response.text();
            console.error(`Error fetching metadata for file ${fileId}: ${errorText}`);
            throw new Error(`Failed to fetch metadata: ${errorText}`);
        } catch (error) {
            console.error(`Error in second URL attempt: ${error.message}`);
            return { success: false, message: error.message || 'Error fetching metadata' };
        }
    } catch (error) {
        console.error(`Error fetching metadata for file ${fileId}:`, error);
        return { success: false, message: error.message || 'Error fetching metadata' };
    }
}

/**
 * Manually process a file
 * @param {string} fileId - The Box file ID
 * @param {string} fileName - The file name
 */
async function processFileManually(fileId, fileName) {
    try {
        console.log(`Manually processing file ${fileName} (ID: ${fileId})...`);
        
        // Show processing indicator
        let fileElement = null;
        document.querySelectorAll('li').forEach(li => {
            if (li.textContent.includes(fileId)) {
                fileElement = li;
            }
        });
        
        if (fileElement) {
            const processingSpan = document.createElement('div');
            processingSpan.className = 'text-sm text-blue-500 mt-1';
            processingSpan.textContent = 'Processing...';
            fileElement.appendChild(processingSpan);
        }
        
        const result = await processFileWithMetadata({
            fileId: fileId,
            fileName: fileName
        });
        
        // Remove processing indicator and show result
        if (fileElement) {
            const processingSpan = fileElement.querySelector('.text-blue-500');
            if (processingSpan) {
                processingSpan.remove();
            }
            
            const resultSpan = document.createElement('div');
            resultSpan.className = result.success ? 'text-sm text-green-500 mt-1' : 'text-sm text-red-500 mt-1';
            resultSpan.textContent = result.message || (result.success ? 'Processed successfully' : 'Processing failed');
            fileElement.appendChild(resultSpan);
        }
        
        // Show metadata in UI if available
        if (result.success && result.metadata && window.displayMetadata) {
            window.displayMetadata(result.metadata, fileId, fileName);
        }
        
        // Refresh the file list to show updated metadata
        const folderIdMatch = window.location.href.match(/folderId=([^&]+)/);
        const folderId = folderIdMatch ? folderIdMatch[1] : '320923621697'; // Default folder ID
        checkUploadedFiles(folderId);
        
        console.log(`Manual processing result for ${fileName}:`, result);
    } catch (error) {
        console.error(`Error manually processing file ${fileName}:`, error);
        alert(`Error processing file: ${error.message}`);
    }
}

/**
 * Format file size in a human-readable format
 * @param {number} bytes - File size in bytes
 * @returns {string} - Formatted file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Update the processing message based on results
 * @param {HTMLElement} div - The processing message container
 * @param {Array} results - Array of processing results
 * @param {boolean} isSuccessful - Whether all processing was successful
 */
function updateProcessingMessage(div, results, isSuccessful) {
    if (isSuccessful) {
        div.innerHTML = `
            <div class="flex items-center">
                <svg class="h-5 w-5 text-green-500 mr-3" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                </svg>
                <span>All documents processed successfully.</span>
            </div>
        `;
        
        // Display a summary of uploaded document types
        let documentTypesSummary = '';
        for (const type in window.documentCounts) {
            documentTypesSummary += `<li>${window.documentCounts[type]} ${type}${window.documentCounts[type] > 1 ? 's' : ''}</li>`;
        }
        
        if (documentTypesSummary) {
            div.innerHTML += `
                <div class="mt-2 text-sm">
                    <p class="font-semibold">Documents uploaded:</p>
                    <ul class="ml-4 list-disc">
                        ${documentTypesSummary}
                    </ul>
                </div>
            `;
        }
        
        // Set timeout to remove the message after 5 seconds
        setTimeout(() => {
            div.remove();
        }, 5000);
    } else {
        // Create a summary of what succeeded and what failed
        const successCount = results.filter(r => r.success).length;
        const failCount = results.length - successCount;
        
        div.innerHTML = `
            <div class="flex items-center mb-2">
                <svg class="h-5 w-5 text-yellow-500 mr-3" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                </svg>
                <span>Document processing completed with some issues (${successCount} succeeded, ${failCount} had issues).</span>
            </div>
            <div class="text-sm text-gray-600 pl-8">
                <p>Your documents have been uploaded successfully, but some metadata processing encountered issues.</p>
            </div>
        `;
        
        // Set timeout to remove the message after 8 seconds
        setTimeout(() => {
            div.remove();
        }, 8000);
    }
}

/**
 * Process multiple files with metadata extraction in a single batch request
 * @param {Array} files - Array of file objects with fileId and fileName
 * @returns {Promise<Object>} - Processing result
 */
async function processBatchFilesWithMetadata(files) {
    try {
        if (!files || !Array.isArray(files) || files.length === 0) {
            console.warn('No files provided for batch processing');
            return { success: false, message: 'No files provided for batch processing' };
        }
        
        console.log(`========== BATCH PROCESSING ${files.length} FILES ==========`);
        
        // Extract file IDs for the batch request
        const fileIds = files.map(file => file.fileId);
        console.log(`File IDs for batch processing:`, fileIds);
        
        // Prepare the request payload
        const payload = {
            fileIds: fileIds,
            templateKey: 'financialDocumentBase'
        };
        
        // Make the batch processing request
        const response = await fetch('/api/box/process-documents-batch/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error(`Failed to process files in batch: ${errorText}`);
            throw new Error(`Failed to process files in batch: ${errorText}`);
        }
        
        const result = await response.json();
        console.log(`Batch processing result:`, result);
        
        // Update the processed files tracking for each file in the batch
        if (result.success && result.results && Array.isArray(result.results)) {
            result.results.forEach(fileResult => {
                if (fileResult.fileId) {
                    // Store the processing result for this file
                    processedFiles.set(fileResult.fileId, {
                        fileName: fileResult.fileName || 'Unknown',
                        fileId: fileResult.fileId,
                        success: fileResult.success || false,
                        message: fileResult.message || 'Unknown status',
                        documentType: fileResult.documentType || null,
                        metadata: fileResult.baseMetadataResult?.data || null,
                        addressValidation: fileResult.address_validation_result || null,
                        processed: true,
                        processingComplete: true
                    });
                    
                    // If document type was identified, update the card
                    if (fileResult.documentType) {
                        console.log(`UPDATING CARD: Document type identified for file ID ${fileResult.fileId}: ${fileResult.documentType}`);
                        updateDocumentCard(fileResult.documentType);
                    }
                    
                    // Log address validation results if available
                    if (fileResult.address_validation_result) {
                        console.log(`ADDRESS VALIDATION RESULT for file ID ${fileResult.fileId}:`, fileResult.address_validation_result);
                        if (fileResult.address_validation_result.success && fileResult.address_validation_result.data) {
                            console.log(`ADDRESS DATA EXTRACTED for file ID ${fileResult.fileId}:`, fileResult.address_validation_result.data);
                        }
                    }
                }
            });
            
            // Save the updated processed files to local storage
            saveProcessedFiles();
        }
        
        return result;
        
    } catch (error) {
        console.error(`Error in batch processing:`, error);
        return {
            success: false,
            message: error.message || 'Error in batch processing',
            error: error
        };
    }
}

async function initiateFinancialSummaryAndRedirect(folderId) {
    console.log(`Initiating financial summary redirection for folder: ${folderId}. API call will be made on next page.`);

    if (!folderId) {
        console.error("Cannot initiate financial summary redirection: folderId is missing.");
        alert("Cannot proceed: Folder information is missing."); // User-facing alert
        return;
    }

    try {
        // Store information in sessionStorage to be picked up by the submission-complete page
        sessionStorage.setItem('summaryGenerationFolderId', folderId);
        // DISABLED: Financial summary generation for demo
        // sessionStorage.setItem('summaryGenerationStatus', 'pending'); // New status
        sessionStorage.setItem('summaryGenerationStatus', 'disabled'); // DEMO: Skip financial summary
        sessionStorage.removeItem('summaryGenerationResult'); // Clear any previous results

        // Redirect immediately to the submission complete page
        // The submission-complete page will now be responsible for making the API call.
        window.location.href = '/submission-complete/'; 
        // Note: if an absolute URL is needed: window.location.origin + '/submission-complete/';

    } catch (error) {
        console.error("Error in initiateFinancialSummaryAndRedirect before redirection:", error);
        // Display an error to the user if something goes wrong before redirection
        alert("An error occurred before preparing the summary generation. Please try again.");
    }
}

/**
 * Process a file for address validation metadata
 * @param {Object} file - File information object with fileId and fileName
 * @returns {Promise<Object>} - Processing result
 */
async function processFileAddressValidation(file) {
    try {
        console.log(`========== PROCESSING ADDRESS VALIDATION FOR FILE ${file.fileId} (${file.fileName}) ==========`);
        console.log(`File details:`, file);
        
        // Step 1: First ensure the address validation template is attached to the file
        console.log(`Ensuring address validation metadata template for file ID ${file.fileId}...`);
        const templateResponse = await fetch(`/api/box/ensure-template?fileId=${file.fileId}&template=address_validation&scope=enterprise_218068865`);
        if (!templateResponse.ok) {
            const errorText = await templateResponse.text();
            console.error(`Failed to ensure address validation template for file ID ${file.fileId}: ${errorText}`);
            throw new Error(`Failed to ensure address validation template: ${errorText}`);
        }
        const templateResult = await templateResponse.json();
        console.log(`Address validation template attachment result for ${file.fileName} (ID: ${file.fileId}):`, templateResult);
        
        // Step 2: Process the document with address validation metadata extraction
        console.log(`Extracting address validation metadata for file ID ${file.fileId}...`);
        let result;
        
        // Use the improved extraction method
        result = await extractAddressValidationMetadata(file.fileId);
        
        if (!result.success) {
            console.error(`Address validation metadata extraction failed for file ID ${file.fileId}:`, result.message);
            throw new Error(`Address validation metadata extraction failed: ${result.message}`);
        }
        
        console.log(`✅ ADDRESS VALIDATION PROCESSING COMPLETE for ${file.fileName}`);
        console.log(`Address validation result:`, result);
        
        return result;
        
    } catch (error) {
        console.error(`Error processing address validation for file ${file.fileName} (ID: ${file.fileId}):`, error);
        return {
            success: false,
            message: error.message,
            fileId: file.fileId,
            fileName: file.fileName
        };
    }
}

/**
 * Extract address validation metadata using Box AI API
 * @param {string} fileId - Box file ID
 * @returns {Promise<Object>} - Response with extraction result
 */
async function extractAddressValidationMetadata(fileId) {
    try {
        console.log(`========== STARTING ADDRESS VALIDATION EXTRACTION FOR FILE ID: ${fileId} ==========`);
        
        // Define the request payload according to Box AI API requirements
        const requestData = {
            metadata_template: {
                template_key: "address_validation",
                type: "metadata_template",
                scope: "enterprise_218068865"  // Using the specific enterprise ID
            },
            items: [{
                id: fileId,
                type: "file"
            }],
            ai_agent: {
                type: "ai_agent_extract_structured",
                long_text: {
                    model: "azure__openai__gpt_4o_mini"
                },
                basic_text: {
                    model: "azure__openai__gpt_4o_mini"
                }
            }
        };
        
        console.log(`Sending address validation extraction request with payload:`, requestData);
        
        // Use fetch API to call our backend, which will forward the request to Box API
        const response = await fetch('/api/box/process-address-validation/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({
                fileId: fileId,
                requestData: requestData
            })
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Address validation API returned error: ${response.status} - ${errorText}`);
        }
        
        const result = await response.json();
        console.log(`Address validation extraction result for file ID ${fileId}:`, result);
        
        return result;
        
    } catch (error) {
        console.error(`Error in address validation extraction for file ID ${fileId}:`, error);
        return {
            success: false,
            message: error.message,
            fileId: fileId
        };
    }
}

/**
 * Manually process a file for address validation
 * @param {string} fileId - The Box file ID
 * @param {string} fileName - The file name
 */
async function processAddressValidationManually(fileId, fileName) {
    try {
        console.log(`Manually processing address validation for file ${fileName} (ID: ${fileId})...`);
        
        // Show processing indicator
        let fileElement = null;
        document.querySelectorAll('li').forEach(li => {
            if (li.textContent.includes(fileId)) {
                fileElement = li;
            }
        });
        
        if (fileElement) {
            const processingSpan = document.createElement('div');
            processingSpan.className = 'text-sm text-blue-500 mt-1';
            processingSpan.textContent = 'Processing address validation...';
            fileElement.appendChild(processingSpan);
        }
        
        const result = await processFileAddressValidation({
            fileId: fileId,
            fileName: fileName
        });
        
        // Remove processing indicator and show result
        if (fileElement) {
            const processingSpan = fileElement.querySelector('.text-blue-500');
            if (processingSpan) {
                processingSpan.remove();
            }
            
            const resultSpan = document.createElement('div');
            resultSpan.className = result.success ? 'text-sm text-green-500 mt-1' : 'text-sm text-red-500 mt-1';
            resultSpan.textContent = result.message || (result.success ? 'Address validation processed successfully' : 'Address validation processing failed');
            fileElement.appendChild(resultSpan);
        }
        
        // Show address metadata in UI if available
        if (result.success && result.extraction_result && result.extraction_result.data && window.displayAddressMetadata) {
            window.displayAddressMetadata(result.extraction_result.data, fileId, fileName);
        }
        
        // Refresh the file list to show updated metadata
        const folderIdMatch = window.location.href.match(/folderId=([^&]+)/);
        const folderId = folderIdMatch ? folderIdMatch[1] : '320923621697'; // Default folder ID
        checkUploadedFiles(folderId);
        
        console.log(`Manual address validation processing result for ${fileName}:`, result);
    } catch (error) {
        console.error(`Error manually processing address validation for file ${fileName}:`, error);
        alert(`Error processing address validation: ${error.message}`);
    }
}

/**
 * Display address metadata in the UI (placeholder function)
 * @param {Object} addressData - The extracted address metadata
 * @param {string} fileId - The file ID
 * @param {string} fileName - The file name
 */
function displayAddressMetadata(addressData, fileId, fileName) {
    console.log(`Displaying address metadata for ${fileName}:`, addressData);
    
    // Check if we have address data to display
    if (!addressData || typeof addressData !== 'object') {
        console.warn('No valid address data to display');
        return;
    }
    
    // Create or update a display area for address metadata
    let addressDisplay = document.getElementById(`address-metadata-${fileId}`);
    if (!addressDisplay) {
        addressDisplay = document.createElement('div');
        addressDisplay.id = `address-metadata-${fileId}`;
        addressDisplay.className = 'mt-2 p-2 bg-gray-100 rounded text-xs';
        
        // Find the file element and append the address display
        document.querySelectorAll('li').forEach(li => {
            if (li.textContent.includes(fileId)) {
                li.appendChild(addressDisplay);
            }
        });
    }
    
    // Build the address display HTML
    let addressHTML = `<strong>Address Information:</strong><br>`;
    
    const addressFields = [
        { key: 'street_address', label: 'Street Address' },
        { key: 'city', label: 'City' },
        { key: 'state_province', label: 'State/Province' },
        { key: 'postal_code', label: 'Postal Code' },
        { key: 'country', label: 'Country' },
        { key: 'full_address', label: 'Full Address' },
        { key: 'validation_status', label: 'Validation Status' },
        { key: 'date_extracted', label: 'Date Extracted' }
    ];
    
    addressFields.forEach(field => {
        if (addressData[field.key] && addressData[field.key] !== '') {
            addressHTML += `<span class="text-gray-600">${field.label}:</span> ${addressData[field.key]}<br>`;
        }
    });
    
    addressDisplay.innerHTML = addressHTML;
}

// Make address validation functions available globally
window.processFileAddressValidation = processFileAddressValidation;
window.extractAddressValidationMetadata = extractAddressValidationMetadata;
window.processAddressValidationManually = processAddressValidationManually;
window.displayAddressMetadata = displayAddressMetadata;