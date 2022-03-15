import os
import os.path
import typing as t

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload


SCOPES: t.Final[str] = ["https://www.googleapis.com/auth/drive"]
"""Permissions to access Google Drive"""

TOKEN_FILE: t.Final[str] = "token.json"
"""Generated file containing OAuth tokens"""

CREDENTIALS_FILE: t.Final[str] = "credentials.json"
"""Downloaded file containing Google Project details and credentials"""

REMOTE_BACKUP_FOLDER_NAME: t.Final[str] = "BackupFolder"
"""Name of the folder to store backups in"""

LOCAL_BACKUP_PATHS: t.Final[list[str]] = ["./backup_test"]
"""Paths to backup"""


creds = None

# Try to login from saved OAuth tokens
if os.path.exists(TOKEN_FILE):
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

# Create new OAuth tokens if they do not exist
if creds is None or not creds.valid:
    if creds is not None and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)

    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())

# Create Google Drive service to interact with
try:
    service = build("drive", "v3", credentials=creds)

    # Query Google Drive for the remote backup folder
    response = (
        service.files()
        .list(
            q=f"name='{REMOTE_BACKUP_FOLDER_NAME}' and mimeType='application/vnd.google-apps.folder'",
            spaces="drive",
        )
        .execute()
    )
    print(f"{response=}")
    # Create remote backup folder if it does not exist
    if not response["files"]:
        file_metdata = {
            "name": REMOTE_BACKUP_FOLDER_NAME,
            "mimeType": "application/vnd.google-apps.folder",
        }

        file = service.files().create(body=file_metdata, fields="id").execute()
        print(file)
        folder_id = file["id"]
    else:
        folder_id = response["files"][0]["id"]
    print(folder_id)
    # Iterate over all the paths and all the files in the paths
    # and upload them to Google Drive

    # for path in LOCAL_BACKUP_PATHS:
    # for file in os.listdir(path):
    for file in os.listdir(LOCAL_BACKUP_PATHS):
        file_metdata = {"name": file, "parents": [folder_id]}

        media = MediaFileUpload(f"{LOCAL_BACKUP_PATHS}/{file}")
        upload_file = (
            service.files()
            .create(body=file_metdata, media_body=media, fields="id")
            .execute()
        )

        # print(f"Backed up {file}")

except HttpError as e:
    print(f"Error: {e}")
