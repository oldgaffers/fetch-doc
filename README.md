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

### 3. Prepare
