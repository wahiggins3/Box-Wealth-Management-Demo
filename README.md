# Horizon Financial Portal

A modern Django web application that transforms a static financial information website into a dynamic, interactive portal with user authentication, account management, document access, and more.

## Features

- **User Authentication**: Secure login/logout functionality and user profiles
- **Dashboard**: Quick overview of financial accounts and summary information
- **Account Management**: View and manage financial accounts with detailed information
- **Document Access**: Integration with Box.com API for secure document storage and retrieval
- **Financial Products**: Browse available financial products and services
- **Support**: Contact form and resources for customer support
- **Responsive Design**: Modern UI using Tailwind CSS for all device sizes

## Technologies Used

- **Backend**: Django (Python web framework)
- **Frontend**: HTML, CSS, JavaScript, Tailwind CSS
- **Authentication**: Django's built-in authentication system
- **Database**: SQLite (default, configurable to other databases)
- **Document Storage**: Box.com API integration
- **UI Components**: Alpine.js for interactive components

## Setup and Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment tool (optional but recommended)

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd financial-portal
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables by creating a `.env` file in the project root based on `.env.example`:
   ```
   # Django Settings
   SECRET_KEY=your-django-secret-key-here
   DEBUG=True
   ALLOWED_HOSTS=localhost,127.0.0.1

   # Box API Settings
   BOX_CLIENT_ID=your-box-client-id
   BOX_CLIENT_SECRET=your-box-client-secret
   BOX_ENTERPRISE_ID=your-box-enterprise-id
   BOX_JWT_KEY_ID=your-box-jwt-key-id
   BOX_PRIVATE_KEY_PATH=/path/to/your/private_key.pem
   BOX_JWT_PRIVATE_KEY_PASSPHRASE=your-passphrase
   ```

5. Run database migrations:
   ```
   python manage.py migrate
   ```

6. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

7. Start the development server:
   ```
   python manage.py runserver
   ```

8. Visit `http://127.0.0.1:8000` in your browser to access the portal.

## Box API Integration

To fully enable document functionality, you'll need to set up a Box application:

1. Create a developer account at [Box Developer Console](https://developer.box.com/)
2. Create a new "Custom App" with "Server Authentication (JWT)"
3. Configure the application with appropriate permissions (at minimum: read/write for content)
4. Download the app's configuration JSON (contains keys, IDs, etc.)
5. Generate a public/private key pair (or use the ones Box generates)
6. Update your `.env` file with the appropriate values from the configuration

## Project Structure

- `portal_project/` - Django project settings and main configuration
- `core/` - Main application with views, URLs, and business logic
- `templates/` - HTML templates for the portal pages
- `static/` - Static files (CSS, JavaScript, images)
- `manage.py` - Django management script

## Development Guidelines

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) coding standards for Python code
- Maintain consistent styling with the existing Tailwind CSS approach
- Use Django's template inheritance to maintain consistent layout
- Document any new features or API integrations

## License

[MIT License](LICENSE)

## Acknowledgements

- Horizon Financial Services (fictional company)
- Box.com for document management API
- Tailwind CSS for styling components

## Box Content Explorer with Metadata View

The documents page now includes an enhanced Box Content Explorer that supports metadata view alongside the traditional files view.

### Features

- **Metadata View**: Displays files in a table format with metadata columns showing document type, issuer, recipient, document date, tax year, and legibility status
- **Files View**: Traditional file browser view for standard file management
- **View Toggle**: Users can switch between metadata and files view using toggle buttons
- **Base Metadata Template**: Uses the `financialDocumentBase` metadata template to display structured information about financial documents

### Implementation Details

- **API Endpoint**: `/api/box/metadata-config/` provides metadata configuration for the Content Explorer
- **Metadata Template**: `enterprise_218068865.financialDocumentBase` 
- **Supported Fields**:
  - Document Type (enum: 1099, W-2, Account Statement, etc.)
  - Issuer Name (string)
  - Recipient Name (string) 
  - Document Date (date)
  - Tax Year (date)
  - Is Legible (enum: Yes/No)

### Usage

1. Navigate to the Documents page
2. Use the "Metadata View" button to see files with their metadata in a table format
3. Use the "Files View" button to switch back to traditional file browser
4. Files must have the base metadata template applied to appear in metadata view

The implementation follows Box's [Content Explorer metadata view documentation](https://developer.box.com/guides/embed/ui-elements/explorer-metadata/) and provides a seamless way to view and manage financial documents with their extracted metadata. 