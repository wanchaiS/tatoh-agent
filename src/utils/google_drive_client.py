import os
from pathlib import Path
from typing import List, Dict, Optional
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
import io
import logging

logger = logging.getLogger(__name__)

# Module-level cache for services
_DRIVE_SERVICE = None
_SHEETS_SERVICE = None

# Scopes needed for both Drive and Sheets (read-only)
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets.readonly'
]

# Public API Functions

def get_image_direct_link(filename: str) -> Optional[str]:
    """
    Finds an image by filename (supports nested paths) and returns a direct link.
    Automatically ensures the file is public.
    """
    file_info = _find_file_by_path(filename)
    if not file_info:
        return None
    
    file_id = file_info['id']
    
    # Direct content link for Messenger compatibility
    return f"https://lh3.googleusercontent.com/d/{file_id}"

def read_markdown(filename: str) -> str:
    """
    Finds a markdown file by filename (supports nested paths) and returns its content.
    """
    file_info = _find_file_by_path(filename)
    if not file_info:
        raise FileNotFoundError(f"Markdown file not found on GDrive: {filename}")
    
    return _read(file_info['id'])

def read_spreadsheet_data(filename: str) -> List[Dict]:
    """
    Finds a spreadsheet by filename (supports nested paths) and returns its data as a list of dicts.
    Always reads the first sheet (A:Z range).
    """
    file_info = _find_file_by_path(filename)
    if not file_info:
        raise FileNotFoundError(f"Spreadsheet not found on GDrive: {filename}")
    
    spreadsheet_id = file_info['id']
    range_name = "A:Z"
    
    return _read_sheet_as_dicts(spreadsheet_id, range_name)

def _get_project_root() -> Path:
    """Finds the project root by searching upwards for a marker file."""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent
    # Fallback to current script directory parents if no marker found
    return current.parent.parent.parent

def _get_drive_service():
    """Helper to initialize Google Drive service as a singleton."""
    global _DRIVE_SERVICE
    if _DRIVE_SERVICE is not None:
        return _DRIVE_SERVICE

    root_path = _get_project_root()
    creds_path = root_path / "google_credentials.json"
    
    if not creds_path.exists():
        raise FileNotFoundError(f"Credentials not found at {creds_path}")

    creds = service_account.Credentials.from_service_account_file(
        str(creds_path), 
        scopes=SCOPES
    )
    _DRIVE_SERVICE = build('drive', 'v3', credentials=creds)
    return _DRIVE_SERVICE

def _get_sheets_service():
    """Helper to initialize Google Sheets service as a singleton."""
    global _SHEETS_SERVICE
    if _SHEETS_SERVICE is not None:
        return _SHEETS_SERVICE

    root_path = _get_project_root()
    creds_path = root_path / "google_credentials.json"
    
    creds = service_account.Credentials.from_service_account_file(
        str(creds_path), 
        scopes=SCOPES
    )
    _SHEETS_SERVICE = build('sheets', 'v4', credentials=creds)
    return _SHEETS_SERVICE

def _list_drive_files(folder_id: Optional[str] = None) -> List[Dict]:
    """
    Internal helper to list files in Google Drive.
    """
    try:
        service = _get_drive_service()
        query = "trashed = false"

        if folder_id:
            query += f" and '{folder_id}' in parents"
            
        results = service.files().list(
            q=query,
            pageSize=50, 
            fields="nextPageToken, files(id, name, mimeType)"
        ).execute()
        
        return results.get('files', [])
    except HttpError as e:
        if e.resp.status == 404:
            raise FileNotFoundError(f"Drive path/folder not found: {folder_id}") from e
        if e.resp.status == 403:
            raise PermissionError(f"Access denied to Drive folder: {folder_id}") from e
        raise RuntimeError(f"Google Drive API error: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error listing Drive files: {e}") from e

def _read(file_id: str) -> str:
    """
    Internal helper to read the content of a Google Drive file by its ID.
    Supports Google Docs (converted to text) and plain text files.
    """
    try:
        service = _get_drive_service()
        
        # Get file metadata to check mimeType
        file_metadata = service.files().get(fileId=file_id).execute()
        mime_type = file_metadata.get('mimeType')

        # Handle Google Docs (export to text)
        if mime_type == 'application/vnd.google-apps.document':
            request = service.files().export_media(fileId=file_id, mimeType='text/plain')
        else:
            # Handle regular files
            request = service.files().get_media(fileId=file_id)

        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        return fh.getvalue().decode('utf-8')
        
    except HttpError as e:
        if e.resp.status == 404:
            raise FileNotFoundError(f"File not found on Drive: {file_id}") from e
        if e.resp.status == 403:
            raise PermissionError(f"Access denied to file: {file_id}") from e
        raise RuntimeError(f"Google Drive API error during read: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error reading file {file_id}: {e}") from e

def _read_sheet(spreadsheet_id: str, range_name: str) -> List[List]:
    """
    Read a range of values from a Google Sheet.
    Returns a list of lists representing the rows.
    """
    try:
        service = _get_sheets_service()
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
        return result.get('values', [])
    except HttpError as e:
        if e.resp.status == 404:
            raise FileNotFoundError(f"Spreadsheet or range not found: {spreadsheet_id} ({range_name})") from e
        if e.resp.status == 403:
            raise PermissionError(f"Access denied to sheet: {spreadsheet_id}") from e
        raise RuntimeError(f"Google Sheets API error: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error reading sheet {spreadsheet_id}: {e}") from e

def _read_sheet_as_dicts(spreadsheet_id: str, range_name: str) -> List[Dict]:
    """
    Read a range of values and convert them into a list of dictionaries.
    Assumes the first row of the range contains the headers.
    """
    rows = _read_sheet(spreadsheet_id, range_name)
    if not rows:
        return []
    
    headers = rows[0]
    data_rows = rows[1:]
    
    result = []
    for row in data_rows:
        # Match each cell to its header. If a row is shorter than headers, fill with None.
        row_dict = {headers[i]: row[i] if i < len(row) else None for i in range(len(headers))}
        result.append(row_dict)
        
    return result

def _find_file_by_path(path: str) -> Optional[Dict]:
    """
    Internal helper to find a file ID by its path (e.g. 'folder/subfolder/file.ext').
    Supports nested folders and files shared with the service account.
    """
    parts = path.strip('/').split('/')
    current_parent_id = None # Start with global search for the first part
    
    service = _get_drive_service()
    
    try:
        for i, part in enumerate(parts):
            is_last = (i == len(parts) - 1)
            
            # Escape single quotes in filename
            escaped_part = part.replace("'", "\\'")
            query = f"name = '{escaped_part}' and trashed = false"
            
            # For the first part, we search globally because it might be shared with us.
            # For subsequent parts, we restrict to the current parent folder.
            if current_parent_id:
                query += f" and '{current_parent_id}' in parents"
            
            results = service.files().list(
                q=query,
                fields="files(id, name, mimeType)"
            ).execute().get('files', [])
            
            if not results:
                logger.warning(f"GDrive search: Part '{part}' of path '{path}' not found.")
                return None
            
            # Take the first match
            match = results[0]
            
            if is_last:
                return match
            else:
                if match['mimeType'] == 'application/vnd.google-apps.folder':
                    current_parent_id = match['id']
                else:
                    # Path continues but current match is not a folder
                    logger.warning(f"GDrive search: Part '{part}' is not a folder but path continues.")
                    return None
    except HttpError as e:
        raise RuntimeError(f"Google Drive API error during path search: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error searching for GDrive path {path}: {e}") from e
    return None
