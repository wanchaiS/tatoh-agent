import os
import sys
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build

def get_drive_service():
    root_path = Path(__file__).resolve().parent
    creds_path = root_path / "google_credentials.json"
    
    if not creds_path.exists():
        print(f"Error: Credentials not found at {creds_path}")
        sys.exit(1)

    creds = service_account.Credentials.from_service_account_file(
        str(creds_path), 
        scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    return build('drive', 'v3', credentials=creds)

def list_files(service, folder_id='root'):
    if folder_id == 'root':
        # List all files accessible to the service account
        query = "trashed = false"
    else:
        # List files inside a specific folder
        query = f"'{folder_id}' in parents and trashed = false"
        
    results = service.files().list(
        q=query,
        pageSize=50,
        fields="nextPageToken, files(id, name, mimeType)"
    ).execute()
    
    return results.get('files', [])

def browse_drive():
    service = get_drive_service()
    current_folder_id = '1RRCSroSKKDU0PKiD1ie4S2jI5nH8DDXD'
    history = []

    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print(f"--- Google Drive Browser ---")
        print(f"Current Folder ID: {current_folder_id}")
        print("-" * 30)
        
        try:
            items = list_files(service, current_folder_id)
            
            if not items:
                print(" (Folder is empty)")
            else:
                for idx, item in enumerate(items):
                    is_folder = item['mimeType'] == 'application/vnd.google-apps.folder'
                    prefix = "[FOLDER]" if is_folder else "[FILE  ]"
                    print(f"{idx + 1}. {prefix} {item['name']} (ID: {item['id']})")
            
            print("-" * 30)
            print("Commands: [number] to enter folder, 'b' to go back, 'q' to quit")
            
            choice = input("\nEnter command: ").strip().lower()
            
            if choice == 'q':
                break
            elif choice == 'b':
                if history:
                    current_folder_id = history.pop()
            elif choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(items):
                    item = items[idx]
                    if item['mimeType'] == 'application/vnd.google-apps.folder':
                        history.append(current_folder_id)
                        current_folder_id = item['id']
                    else:
                        print(f"\nSelected File: {item['name']}")
                        print(f"MimeType: {item['mimeType']}")
                        input("\nPress Enter to continue...")
                else:
                    print("Invalid number.")
                    input("Press Enter...")
            else:
                print("Invalid command.")
                input("Press Enter...")
                
        except Exception as e:
            print(f"An error occurred: {e}")
            input("\nPress Enter to return to root...")
            current_folder_id = 'root'
            history = []

if __name__ == '__main__':
    browse_drive()
