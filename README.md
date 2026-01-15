# Google Docs to HTML Lambda Function

AWS Lambda function that fetches private Google Docs by name from a shared folder and returns them as HTML using Google service account authentication.

## Features

- 🔐 **Secure Authentication** - Uses Google Cloud service account for private document access
- 📁 **Folder-based Search** - Searches for documents by name within a specified shared folder
- 🎨 **HTML Conversion** - Converts Google Docs structure to clean, styled HTML
- ✨ **Rich Formatting Support** - Handles headings, paragraphs, bold, italic, underline, and tables
- 🌐 **CORS Enabled** - Ready for web application integration
- ⚡ **Serverless** - Fully managed AWS Lambda deployment

## Prerequisites

- AWS Account with Lambda access
- Google Cloud Platform account
- Python 3.9 or higher

## Google Cloud Setup

### 1. Create a Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select an existing one
3. Navigate to **APIs & Services** → **Library**
4. Enable the following APIs:
   - Google Docs API
   - Google Drive API
5. Go to **IAM & Admin** → **Service Accounts**
6. Click **Create Service Account**
7. Give it a name (e.g., "lambda-docs-reader")
8. Grant it the **Viewer** role (optional)
9. Click **Done**
10. Click on the created service account
11. Go to **Keys** tab → **Add Key** → **Create New Key**
12. Choose **JSON** format and download the key file

### 2. Share Your Google Drive Folder

1. Open Google Drive and navigate to the folder containing your documents
2. Right-click the folder → **Share**
3. Add the service account email (found in the JSON key file, e.g., `your-service@project-id.iam.gserviceaccount.com`)
4. Grant **Viewer** access
5. Copy the folder ID from the URL:
   ```
   https://drive.google.com/drive/folders/1a2b3c4d5e6f7g8h9i0j
                                         ^^^^^^^^^^^^^^^^^^^^
                                         This is your folder ID
   ```

### 3. Prepare Credentials

Encode your service account JSON key as base64:

```bash
# On macOS/Linux
base64 -i service-account-key.json | tr -d '\n' > encoded-credentials.txt

# On Windows (PowerShell)
[Convert]::ToBase64String([IO.File]::ReadAllBytes("service-account-key.json")) | Out-File -Encoding ASCII encoded-credentials.txt
```

## AWS Lambda Deployment

### 1. Create Lambda Layer for Dependencies

Create a deployment package with required libraries:

```bash
# Create directory structure
mkdir -p lambda-layer/python
cd lambda-layer

# Install dependencies
pip install google-auth google-auth-httplib2 google-api-python-client -t python/

# Create ZIP file
zip -r google-api-layer.zip python/
```

Upload the layer:
1. Go to AWS Lambda Console → **Layers** → **Create Layer**
2. Upload `google-api-layer.zip`
3. Compatible runtimes: Python 3.9, 3.10, 3.11, 3.12

### 2. Create Lambda Function

1. Go to AWS Lambda Console → **Create Function**
2. Choose **Author from scratch**
3. Function name: `google-docs-to-html`
4. Runtime: **Python 3.9** (or higher)
5. Click **Create Function**

### 3. Add the Code

Copy the Lambda function code into the inline editor or upload as a ZIP file.

### 4. Attach the Layer

1. In your function, scroll to **Layers** section
2. Click **Add a layer**
3. Choose **Custom layers**
4. Select your `google-api-layer`
5. Click **Add**

### 5. Configure Environment Variables

Add the following environment variables:

| Key | Value | Description |
|-----|-------|-------------|
| `GOOGLE_CREDENTIALS_JSON` | Base64-encoded JSON | Contents of `encoded-credentials.txt` |
| `GOOGLE_DRIVE_FOLDER_ID` | Folder ID string | The shared folder ID from Google Drive |

### 6. Adjust Function Settings

- **Memory**: 256 MB (recommended)
- **Timeout**: 30 seconds
- **Execution role**: Use default or create a role with basic Lambda execution permissions

### 7. Test the Function

Create a test event:

```json
{
  "doc_name": "Your Document Name"
}
```

Click **Test** and verify the response contains HTML content.

## Usage

### Direct Lambda Invocation

```json
{
  "doc_name": "Meeting Notes"
}
```

### API Gateway Integration

If you expose the Lambda via API Gateway:

**GET Request:**
```
https://your-api-gateway-url/docs?doc_name=Meeting%20Notes
```

**POST Request:**
```bash
curl -X POST https://your-api-gateway-url/docs \
  -H "Content-Type: application/json" \
  -d '{"doc_name": "Meeting Notes"}'
```

### Response Format

**Success (200):**
```html
<!DOCTYPE html>
<html>
<head>
  <title>Meeting Notes</title>
  ...
</head>
<body>
  <h1>Meeting Notes</h1>
  <p>Document content...</p>
</body>
</html>
```

**Error (400/404/500):**
```json
{
  "error": "Document \"Meeting Notes\" not found in the specified folder"
}
```

## Error Handling

The function returns appropriate HTTP status codes:

- **200** - Success, returns HTML
- **400** - Bad request (missing `doc_name` parameter)
- **403** - Access denied (service account lacks permissions)
- **404** - Document not found in folder
- **500** - Internal server error (configuration or API error)

## Troubleshooting

### "Access denied" errors
- Verify the folder is shared with the service account email
- Ensure both Google Docs API and Google Drive API are enabled
- Check that the service account has Viewer access

### "Document not found" errors
- Document name must match exactly (case-sensitive)
- Document must be a Google Doc (not PDF, Word, etc.)
- Document must be in the specified folder (not in subfolders)

### "Credentials error" errors
- Verify base64 encoding is correct and has no line breaks
- Ensure the JSON key file is valid and not expired
- Check the `GOOGLE_CREDENTIALS_JSON` environment variable is set correctly

### Import errors
- Verify the Lambda layer is attached correctly
- Ensure the layer structure is `python/` directory at root
- Check Lambda runtime matches layer compatibility

## Limitations

- Only searches the root of the specified folder (not subfolders)
- Returns first match if multiple documents have the same name
- Basic HTML conversion (advanced formatting may not be fully preserved)
- Document name must be an exact match (case-sensitive)
