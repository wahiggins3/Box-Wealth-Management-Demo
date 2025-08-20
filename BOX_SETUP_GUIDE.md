# Box Integration Setup Guide

This guide will walk you through setting up Box API integration for the Financial Portal.

## Prerequisites

1. A Box Developer account (sign up at [Box Developer Console](https://developer.box.com))
2. Admin access to your Box enterprise account

## Step 1: Create a Box App

1. Log in to the [Box Developer Console](https://app.box.com/developers/console)
2. Click "Create New App"
3. Select "Custom App" as the app type
4. Select "Server Authentication (with JWT)" as the authentication method
5. Name your app (e.g., "Financial Portal Integration")
6. Click "Create App"

## Step 2: Configure App Settings

After creating your app, configure the following settings:

1. Under "App Access Level," select "App + Enterprise Access"
2. Under "Application Scopes," enable the following:
   - Read and write all files and folders stored in Box
   - Manage users
   - Manage groups
   - Manage enterprise properties

3. Under "Advanced Features," enable:
   - Make API calls using the as-user header
   - Generate user access tokens

4. Click "Save Changes"

## Step 3: Generate Developer Token & Download Configuration

1. Under "Configuration," find the "Developer Token" section
2. Click "Generate Developer Token" (note: this token is temporary)
3. Click "Download as JSON" to download your app configuration

## Step 4: Generate Public/Private Key Pair

1. Under the "Configuration" tab, scroll to "Add and Manage Public Keys"
2. Click "Generate a Public/Private Keypair"
3. This will download a JSON file containing your public and private keys
4. Keep this file secure as it contains your private key

## Step 5: Extract Private Key

1. Extract the `private_key` from the downloaded JSON file
2. Save this as a .pem file (e.g., `box_private_key.pem`)
3. Store this file in a secure location on your server

## Step 6: Configure Environment Variables

You need to set the following environment variables for the Box integration to work:

```
BOX_CLIENT_ID=<your_client_id>
BOX_CLIENT_SECRET=<your_client_secret>
BOX_ENTERPRISE_ID=<your_enterprise_id>
BOX_JWT_KEY_ID=<your_jwt_key_id>
BOX_PRIVATE_KEY_PATH=<path_to_your_private_key.pem>
BOX_JWT_PRIVATE_KEY_PASSPHRASE=<your_passphrase_if_exists>
```

You can use the `simple_box_setup.py` script to generate the .env file. Edit the script and fill in your values.

## Step 7: Testing the Integration

1. Run the Box configuration test script:
   ```
   python box_config_test.py
   ```

2. Start your Django development server:
   ```
   python manage.py runserver
   ```

3. Navigate to the Documents tab to test the integration

## Troubleshooting

Common issues and their solutions:

### Authentication Failed
- Ensure your private key and JWT Key ID match
- Check that your enterprise ID is correct
- Verify your app has the necessary permissions

### "Key ID header parameter must be a string"
- Make sure your JWT Key ID is properly formatted as a string
- Check that there are no extra whitespace characters

### Private Key Issues
- Ensure the private key file is readable by the application
- If your key is encrypted, provide the correct passphrase
- Verify the private key is in PEM format

### General Connectivity Issues
- Check your network connectivity to Box API (box.com)
- Ensure your firewall allows outbound connections to Box API

## Additional Resources

- [Box Developer Documentation](https://developer.box.com/documentation/)
- [Box JWT Authentication](https://developer.box.com/guides/authentication/jwt/)
- [Box Content API Reference](https://developer.box.com/reference/) 