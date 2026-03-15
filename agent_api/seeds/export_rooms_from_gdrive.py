#!/usr/bin/env python3
"""
Export room data from Google Sheets to JSON for seeding Postgres.
Run from agent_api/: python seeds/export_rooms_from_gdrive.py
"""

import json
import sys
import io
import logging
from pathlib import Path
from typing import Dict, List, Optional

# Google Drive imports
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# Google Drive / Sheets API constants
SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]


def _get_project_root() -> Path:
    """Finds the project root by searching upwards for a marker file."""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent
    return current.parent.parent.parent


def _get_sheets_service():
    """Initialize Google Sheets service."""
    root_path = _get_project_root()
    creds_path = root_path / "google_credentials.json"

    if not creds_path.exists():
        raise FileNotFoundError(f"Credentials not found at {creds_path}")

    creds = service_account.Credentials.from_service_account_file(
        str(creds_path), scopes=SCOPES
    )
    return build("sheets", "v4", credentials=creds)


def _get_drive_service():
    """Initialize Google Drive service."""
    root_path = _get_project_root()
    creds_path = root_path / "google_credentials.json"

    if not creds_path.exists():
        raise FileNotFoundError(f"Credentials not found at {creds_path}")

    creds = service_account.Credentials.from_service_account_file(
        str(creds_path), scopes=SCOPES
    )
    return build("drive", "v3", credentials=creds)


def _list_drive_files(folder_id: Optional[str] = None) -> List[Dict]:
    """Internal helper to list files in Google Drive."""
    try:
        service = _get_drive_service()
        query = "trashed = false"

        if folder_id:
            query += f" and '{folder_id}' in parents"

        results = (
            service.files()
            .list(
                q=query, pageSize=50, fields="nextPageToken, files(id, name, mimeType)"
            )
            .execute()
        )

        return results.get("files", [])
    except HttpError as e:
        if e.resp.status == 404:
            raise FileNotFoundError(f"Drive path/folder not found: {folder_id}") from e
        if e.resp.status == 403:
            raise PermissionError(f"Access denied to Drive folder: {folder_id}") from e
        raise RuntimeError(f"Google Drive API error: {e}") from e


def _find_file_by_path(path: str) -> Optional[Dict]:
    """Internal helper to find a file ID by its path."""
    parts = path.strip("/").split("/")
    current_parent_id = None

    service = _get_drive_service()

    try:
        for i, part in enumerate(parts):
            is_last = i == len(parts) - 1
            escaped_part = part.replace("'", "\\'")
            query = f"name = '{escaped_part}' and trashed = false"

            if current_parent_id:
                query += f" and '{current_parent_id}' in parents"

            results = (
                service.files()
                .list(q=query, fields="files(id, name, mimeType)")
                .execute()
                .get("files", [])
            )

            if not results:
                logger.warning(
                    f"GDrive search: Part '{part}' of path '{path}' not found."
                )
                return None

            match = results[0]

            if is_last:
                return match
            else:
                if match["mimeType"] == "application/vnd.google-apps.folder":
                    current_parent_id = match["id"]
                else:
                    logger.warning(
                        f"GDrive search: Part '{part}' is not a folder but path continues."
                    )
                    return None
    except HttpError as e:
        raise RuntimeError(f"Google Drive API error during path search: {e}") from e

    return None


def _read_sheet(spreadsheet_id: str, range_name: str) -> List[List]:
    """Read a range of values from a Google Sheet."""
    try:
        service = _get_sheets_service()
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=spreadsheet_id, range=range_name)
            .execute()
        )
        return result.get("values", [])
    except HttpError as e:
        if e.resp.status == 404:
            raise FileNotFoundError(
                f"Spreadsheet or range not found: {spreadsheet_id} ({range_name})"
            ) from e
        if e.resp.status == 403:
            raise PermissionError(f"Access denied to sheet: {spreadsheet_id}") from e
        raise RuntimeError(f"Google Sheets API error: {e}") from e


def _read_sheet_as_dicts(spreadsheet_id: str, range_name: str) -> List[Dict]:
    """Read a range of values and convert them into a list of dictionaries."""
    rows = _read_sheet(spreadsheet_id, range_name)
    if not rows:
        return []

    headers = rows[0]
    data_rows = rows[1:]

    result = []
    for row in data_rows:
        row_dict = {
            headers[i]: row[i] if i < len(row) else None for i in range(len(headers))
        }
        result.append(row_dict)

    return result


def read_spreadsheet_data(path: str) -> List[Dict]:
    """Finds a spreadsheet by filename and returns its data as a list of dicts."""
    file_info = _find_file_by_path(path)
    if not file_info:
        raise FileNotFoundError(f"Spreadsheet not found on GDrive: {path}")

    spreadsheet_id = file_info["id"]
    range_name = "A:Z"

    return _read_sheet_as_dicts(spreadsheet_id, range_name)


def parse_int(value, default=0):
    """Parse a value as integer, with fallback."""
    if value is None or value == "":
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def parse_float(value, default=0.0):
    """Parse a value as float, with fallback."""
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def export_rooms():
    """Fetch room data from Google Sheets and export to JSON."""
    try:
        print("Fetching rooms data from Google Sheets...")
        raw_data = read_spreadsheet_data("/cooper-project/data/rooms_info")

        if not raw_data:
            print("No room data found in Google Sheets.")
            return

        print(f"Found {len(raw_data)} rooms. Processing...")

        rooms = []
        for row in raw_data:
            # Map Google Sheets columns to Postgres Room model fields
            room = {
                "room_name": row.get("room_name", "").strip(),
                "room_type": row.get("room_type", "").strip(),
                "summary": row.get("summary", "").strip(),
                "bed_queen": 0,  # Default - user will fill in manually
                "bed_single": 0,  # Default - user will fill in manually
                "baths": parse_int(row.get("baths")),
                "size": parse_float(row.get("size")),
                "price_weekdays": parse_float(row.get("price_weekdays")),
                "price_weekends_holidays": parse_float(row.get("price_weekends_holidays")),
                "price_ny_songkran": parse_float(row.get("price_ny_songkran")),
                "max_guests": parse_int(row.get("max_guests")),
                "steps_to_beach": parse_int(row.get("steps_to_beach")),
                "sea_view": parse_int(row.get("sea_view")),
                "privacy": parse_int(row.get("privacy")),
                "steps_to_restaurant": parse_int(row.get("steps_to_restaurant")),
                "room_design": parse_int(row.get("room_design")),
                "room_newness": parse_int(row.get("room_newness")),
                "tags": row.get("tags", "").strip() if row.get("tags") else None,
            }

            # Skip rooms with missing room_name
            if not room["room_name"]:
                print(f"Skipping row with missing room_name: {row}")
                continue

            rooms.append(room)

        # Write to JSON file
        output_path = Path(__file__).parent / "rooms.json"
        with open(output_path, "w") as f:
            json.dump(rooms, f, indent=2)

        print(f"✓ Exported {len(rooms)} rooms to {output_path}")

    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Make sure google_credentials.json exists in the project root.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    export_rooms()
