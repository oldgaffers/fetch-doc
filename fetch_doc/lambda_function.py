"""
Google Docs to HTML AWS Lambda Function

Created with assistance from Claude (Anthropic)
Date: January 2026

This function uses the following Google APIs and libraries:
- Google Docs API v1 (https://developers.google.com/docs/api)
- Google Drive API v3 (https://developers.google.com/drive/api)
- google-auth library (https://github.com/googleapis/google-auth-library-python)
- google-api-python-client (https://github.com/googleapis/google-api-python-client)

Dependencies:
- google-auth: Apache License 2.0
- google-auth-httplib2: Apache License 2.0
- google-api-python-client: Apache License 2.0

References:
- Google Docs API Documentation: https://developers.google.com/docs/api/reference/rest
- Google Drive API Documentation: https://developers.google.com/drive/api/reference/rest/v3
- Service Account Authentication: https://cloud.google.com/iam/docs/service-accounts
"""

import json
import os
import base64
from typing import Dict, Any, Optional

# These will need to be installed as a Lambda layer
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Fetches a private Google Doc by name from a shared folder and returns it as HTML.
    
    Required environment variables:
    - GOOGLE_CREDENTIALS_JSON: Base64-encoded service account JSON credentials
    - GOOGLE_DRIVE_FOLDER_ID: The ID of the shared folder to search in
    
    Expected event format:
    {
        "doc_name": "My Document Name"
    }
    
    Or via query parameters:
    {
        "queryStringParameters": {
            "doc_name": "My Document Name"
        }
    }
    """
    
    try:
        # Extract doc_name from event
        doc_name = None
        
        if 'doc_name' in event:
            doc_name = event['doc_name']
        elif 'queryStringParameters' in event and event['queryStringParameters']:
            doc_name = event['queryStringParameters'].get('doc_name')
        elif 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
            doc_name = body.get('doc_name')
        
        if not doc_name:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'error': 'Missing doc_name parameter'
                })
            }
        
        # Get credentials from environment variable
        credentials_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
        if not credentials_json:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'error': 'GOOGLE_CREDENTIALS_JSON environment variable not set'
                })
            }
        
        # Get folder ID from environment variable
        folder_id = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')
        if not folder_id:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'error': 'GOOGLE_DRIVE_FOLDER_ID environment variable not set'
                })
            }
        
        # Decode base64 credentials
        try:
            credentials_data = json.loads(base64.b64decode(credentials_json))
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'error': f'Failed to decode credentials: {str(e)}'
                })
            }
        
        # Create credentials object with both Drive and Docs scopes
        SCOPES = [
            'https://www.googleapis.com/auth/documents.readonly',
            'https://www.googleapis.com/auth/drive.readonly'
        ]
        credentials = service_account.Credentials.from_service_account_info(
            credentials_data, 
            scopes=SCOPES
        )
        
        # Build the Google Drive API service
        drive_service = build('drive', 'v3', credentials=credentials)
        
        # Search for the document by name in the specified folder
        doc_id = find_document_in_folder(drive_service, doc_name, folder_id)
        
        if not doc_id:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'error': f'Document "{doc_name}" not found in the specified folder'
                })
            }
        
        # Build the Google Docs API service
        docs_service = build('docs', 'v1', credentials=credentials)
        
        # Fetch the document
        document = docs_service.documents().get(documentId=doc_id).execute()
        
        # Convert document to HTML
        html_content = convert_google_doc_to_html(document)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'text/html',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
            },
            'body': html_content
        }
        
    except HttpError as e:
        error_message = f'Google API Error: {e.resp.status} - {e.error_details}'
        if e.resp.status == 404:
            error_message = 'Document not found'
        elif e.resp.status == 403:
            error_message = 'Access denied. Service account may not have permission to access this document or folder'
        
        return {
            'statusCode': e.resp.status,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': error_message
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': f'Internal server error: {str(e)}'
            })
        }


def find_document_in_folder(drive_service, doc_name: str, folder_id: str) -> Optional[str]:
    """
    Searches for a Google Doc by name within a specific folder.
    Returns the document ID if found, None otherwise.
    """
    try:
        # Search for files with the exact name in the specified folder
        # Only look for Google Docs (mimeType)
        query = f"name = '{doc_name}' and '{folder_id}' in parents and mimeType = 'application/vnd.google-apps.document' and trashed = false"
        
        results = drive_service.files().list(
            q=query,
            spaces='drive',
            fields='files(id, name)',
            pageSize=10
        ).execute()
        
        files = results.get('files', [])
        
        if not files:
            return None
        
        # If multiple files with the same name exist, return the first one
        # You could add logic here to handle duplicates differently
        return files[0]['id']
        
    except HttpError as e:
        print(f'Error searching for document: {e}')
        return None


def convert_google_doc_to_html(document: Dict) -> str:
    """
    Converts a Google Docs API document structure to HTML.
    This is a basic implementation that handles common elements.
    """
    title = document.get('title', 'Untitled Document')
    body = document.get('body', {})
    content = body.get('content', [])
    
    html_parts = [
        '<!DOCTYPE html>',
        '<html>',
        '<head>',
        f'<title>{title}</title>',
        '<meta charset="UTF-8">',
        '<style>',
        'body { font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; line-height: 1.6; }',
        'h1 { font-size: 24px; margin-top: 20px; margin-bottom: 10px; }',
        'h2 { font-size: 20px; margin-top: 18px; margin-bottom: 8px; }',
        'h3 { font-size: 16px; margin-top: 16px; margin-bottom: 6px; }',
        'p { margin: 10px 0; }',
        'ul, ol { margin: 10px 0; padding-left: 30px; }',
        'li { margin: 5px 0; }',
        '.bold { font-weight: bold; }',
        '.italic { font-style: italic; }',
        '.underline { text-decoration: underline; }',
        '</style>',
        '</head>',
        '<body>',
        f'<h1>{title}</h1>'
    ]
    
    for element in content:
        if 'paragraph' in element:
            paragraph = element['paragraph']
            para_elements = paragraph.get('elements', [])
            
            # Check if this is a heading
            paragraph_style = paragraph.get('paragraphStyle', {})
            named_style = paragraph_style.get('namedStyleType', 'NORMAL_TEXT')
            
            # Build paragraph content
            text_parts = []
            for elem in para_elements:
                if 'textRun' in elem:
                    text_run = elem['textRun']
                    content_text = text_run.get('content', '')
                    text_style = text_run.get('textStyle', {})
                    
                    # Apply text styles
                    styled_text = content_text
                    if text_style.get('bold'):
                        styled_text = f'<span class="bold">{styled_text}</span>'
                    if text_style.get('italic'):
                        styled_text = f'<span class="italic">{styled_text}</span>'
                    if text_style.get('underline'):
                        styled_text = f'<span class="underline">{styled_text}</span>'
                    
                    text_parts.append(styled_text)
            
            combined_text = ''.join(text_parts).strip()
            
            if combined_text:
                if named_style == 'HEADING_1':
                    html_parts.append(f'<h1>{combined_text}</h1>')
                elif named_style == 'HEADING_2':
                    html_parts.append(f'<h2>{combined_text}</h2>')
                elif named_style == 'HEADING_3':
                    html_parts.append(f'<h3>{combined_text}</h3>')
                else:
                    html_parts.append(f'<p>{combined_text}</p>')
        
        elif 'table' in element:
            # Basic table support
            html_parts.append('<table border="1" cellpadding="5" cellspacing="0">')
            table = element['table']
            for row in table.get('tableRows', []):
                html_parts.append('<tr>')
                for cell in row.get('tableCells', []):
                    cell_content = []
                    for cell_elem in cell.get('content', []):
                        if 'paragraph' in cell_elem:
                            para_elems = cell_elem['paragraph'].get('elements', [])
                            for pe in para_elems:
                                if 'textRun' in pe:
                                    cell_content.append(pe['textRun'].get('content', ''))
                    html_parts.append(f'<td>{"".join(cell_content).strip()}</td>')
                html_parts.append('</tr>')
            html_parts.append('</table>')
    
    html_parts.extend([
        '</body>',
        '</html>'
    ])
    
    return '\n'.join(html_parts)
