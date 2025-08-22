# Box Wealth Onboarding Demo

A comprehensive Django web application showcasing **Box.com AI integration** for financial document processing and wealth management onboarding. This demo platform demonstrates real-time document classification using custom Box AI agents and provides an educational interface for understanding AI-powered document workflows.

## 🎯 Demo Purpose

This application serves as a **complete demonstration platform** for:
- **Box AI Agent Integration** - Custom Google Gemini 2.5 Pro document classifier
- **Real-time Document Processing** - Upload and classify financial documents instantly  
- **Educational Transparency** - Debug mode showing AI requests/responses
- **Professional UI** - Clean, branded interface perfect for client presentations
- **End-to-End Workflow** - From user onboarding to document classification

## 🚀 Key Features

### 📄 **Box AI Document Classification**
- **Custom AI Agent**: "Financial Document Classifier" using Google Gemini 2.5 Pro
- **Real-time Processing**: Documents classified instantly upon upload
- **Document Types**: 1099, W-2, Account Statements, Mortgage Statements, Trust Documents, Asset Lists, 1040, Personal Financial Statements, Life Insurance Documents
- **Visual Feedback**: Document cards turn green with counts when classified
- **Session Tracking**: Only shows files uploaded in current session

### 🔍 **Educational Debug Mode**
- **Toggle Debug View**: Show/hide AI agent interactions in real-time
- **Request Inspection**: View exact API calls sent to Box AI agent
- **Response Analysis**: See raw JSON responses from Google Gemini 2.5 Pro
- **Processing Flow**: Step-by-step visibility into classification workflow
- **Perfect for Demos**: Technical transparency for educational presentations

### 📁 **Box Content Integration**
- **Content Explorer**: Browse and manage documents with Box UI elements
- **Content Uploader**: Drag-and-drop file uploads directly to Box
- **Dynamic Folders**: Auto-creates client folders based on user names
- **Folder Structure**: Organized with "Shared with Advisor" subfolders
- **Downscoped Tokens**: Secure, limited-permission access tokens

### 🎨 **Professional UI/UX**
- **Box Branding**: Clear "Powered and secured by Box.com" identification
- **Horizon Financial Services**: Complete branded experience
- **Responsive Design**: Works on all devices
- **Dynamic Expansion**: Document viewer can expand for better preview
- **Clean Styling**: Professional appearance perfect for client demos

## 🛠 Technologies Used

- **Backend**: Django (Python web framework)
- **AI Integration**: Box AI with Google Gemini 2.5 Pro
- **Document Storage**: Box.com API with JWT authentication
- **Frontend**: HTML, CSS, JavaScript, Tailwind CSS
- **Box UI Elements**: Content Explorer, Content Uploader, Content Preview
- **Authentication**: Django's built-in authentication system
- **Database**: SQLite with custom onboarding models

## ⚙️ Setup and Installation

### Prerequisites

- Python 3.12 or higher
- Box Developer Account with Custom App (Server Authentication/JWT)
- Box AI Agent configured (Financial Document Classifier)

### Quick Setup

1. **Clone and Setup Environment**:
   ```bash
   git clone <repository-url>
   cd BoxWealthOnboardingDemo
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure Box Integration**:
   - Create Box Custom App with Server Authentication (JWT)
   - Download app configuration JSON
   - Run setup script:
   ```bash
   python setup_env_from_json.py your-box-config.json
   ```

3. **Database Setup**:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

4. **Start Demo**:
   ```bash
   python manage.py runserver
   ```

Visit `http://127.0.0.1:8000` to access the demo.

## 🔧 Box.com Integration Points

### 🤖 **AI Agent Configuration**

**Agent Details**:
- **Name**: Financial Document Classifier  
- **ID**: 36769377
- **Model**: Google Gemini 2.5 Pro
- **Type**: ai_agent_ask

**Prompt Template**:
```
Analyze this financial document and classify it. Respond ONLY with valid JSON in this exact format:
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
- "Other" - Financial documents not matching above categories
```

### 🔐 **Authentication & Security**

**JWT Authentication**:
```python
# Environment Variables Required
BOX_CLIENT_ID=your-box-client-id
BOX_CLIENT_SECRET=your-box-client-secret  
BOX_ENTERPRISE_ID=your-box-enterprise-id
BOX_JWT_KEY_ID=your-box-jwt-key-id
BOX_PRIVATE_KEY_PATH=path/to/private_key.pem
BOX_JWT_PRIVATE_KEY_PASSPHRASE=your-passphrase
```

**Required Box Permissions**:
- Write all files and folders stored in Box
- Manage metadata on files and folders
- Manage enterprise properties
- Generate user access tokens
- Perform Actions as Users

### 📊 **API Endpoints**

| Endpoint | Purpose | Box Integration |
|----------|---------|-----------------|
| `/api/box/client-folder/` | Create/get client folders | Folder API |
| `/api/box/explorer-token/` | Generate downscoped tokens | Token API |
| `/api/box/process-documents-batch/` | AI classification | AI Ask API |
| `/api/box/check-uploads/` | List folder contents | Files API |

### 🎛 **Box Admin Console Setup**

**Required Settings**:
1. **App Authorization**: Authorize app in Box Admin Console
2. **CORS Domains**: Add your domain (e.g., `http://127.0.0.1:8000`)
3. **Dedicated Scopes**: Enable for downscoped tokens
4. **AI Access**: Ensure AI features are enabled for your enterprise

## 📋 Demo Workflow

### 👤 **User Journey**
1. **Registration**: New user creates account
2. **Wealth Onboarding**: Complete onboarding form with name/details
3. **Folder Creation**: Box folders auto-created based on user name
4. **Document Upload**: Upload financial documents via Box widget
5. **AI Classification**: Documents automatically classified by AI agent
6. **Visual Feedback**: Document cards update with classification results

### 🔍 **Debug Mode Demo**
1. **Enable Debug**: Toggle debug mode on upload page
2. **Upload Document**: Watch real-time AI processing
3. **View Request**: See exact API call to Box AI agent
4. **Analyze Response**: Inspect Google Gemini 2.5 Pro classification
5. **UI Updates**: Observe how classification updates document cards

## 📁 Project Structure

```
BoxWealthOnboardingDemo/
├── core/                          # Main Django app
│   ├── models.py                  # User onboarding models
│   ├── views.py                   # Box integration views
│   ├── services/                  # Box service layer
│   │   ├── box_metadata_extraction.py    # AI agent integration
│   │   ├── document_processing_service.py # Workflow orchestration
│   │   └── box_webhook_handler.py         # Webhook processing
├── templates/                     # HTML templates
│   ├── documents.html             # Box Content Explorer
│   ├── document_upload.html       # Box Content Uploader + Debug
│   ├── wealth_onboarding.html     # User onboarding form
├── static/
│   ├── js/document_processing.js  # Box UI + AI integration
│   ├── images/                    # Horizon Financial branding
└── portal_project/                # Django settings
```

## 🎓 Educational Value

This demo showcases:
- **Box AI Integration**: Real-world implementation of custom AI agents
- **API Architecture**: Proper service layer separation and error handling  
- **UI/UX Design**: Professional interface with educational transparency
- **Security Patterns**: JWT authentication and downscoped tokens
- **Workflow Automation**: End-to-end document processing pipeline

## 🔧 Development Notes

### Custom Features Added
- **Demo Mode**: Skips metadata storage, focuses on UI updates
- **Session Tracking**: JavaScript Map for current session files
- **Dynamic UI**: Expandable document viewer with manual controls
- **Cache Busting**: Template versioning for development
- **Error Handling**: Graceful fallbacks for Box API issues

### Box UI Customization
- **Logo Integration**: Custom Horizon Financial branding in Box widgets
- **Border Styling**: Clean blue borders identifying Box components
- **Event Handling**: Upload listeners for automatic processing
- **Token Management**: Automatic refresh and scoping

## 📞 Support

For Box.com integration questions:
- [Box Developer Documentation](https://developer.box.com/)
- [Box AI Documentation](https://developer.box.com/guides/box-ai/)
- [Box UI Elements](https://developer.box.com/guides/embed/ui-elements/)

## 🏢 About

**Horizon Financial Services** - A fictional wealth management company used for demonstration purposes.

This project demonstrates enterprise-grade Box.com integration with AI-powered document processing, perfect for financial services, legal firms, or any organization requiring intelligent document classification and management.

---

**🎯 Ready for Demo!** This platform provides a complete, professional demonstration of Box AI capabilities with full educational transparency.