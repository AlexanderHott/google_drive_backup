import glob
import os
import os.path
import threading
import typing as t

import rich
from rich.progress import (
    BarColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
)

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

LOCAL_BACKUP_PATHS: t.Final[list[str]] = ["backup_test"]
"""Paths to backup"""


def get_recursive_file_count(path: str) -> int:
    """Get the number of files recursivly in a directory"""
    count = 0
    for root, dirs, files in os.walk(path):
        count += len(files)
        for dir in dirs:
            count += get_recursive_file_count(dir)
    return count


def upload_file(task_id: TaskID, file: str, folder_id: str) -> None:
    if os.path.isdir(file):
        return
    progress.console.log(f"Uploading {file}")

    file_metdata = {"name": file, "parents": [folder_id]}
    media = MediaFileUpload(file)
    service.files().create(body=file_metdata, media_body=media, fields="id").execute()
    progress.advance(task_id)
    progress.console.log(f"Completed uploading {file}")


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
    # Create remote backup folder if it does not exist
    if not response["files"]:
        file_metdata = {
            "name": REMOTE_BACKUP_FOLDER_NAME,
            "mimeType": "application/vnd.google-apps.folder",
        }

        file = service.files().create(body=file_metdata, fields="id").execute()
        folder_id = file["id"]
    else:
        folder_id = response["files"][0]["id"]
    # Iterate over all the paths and all the files in the paths
    # and upload them to Google Drive

    total_files = sum([get_recursive_file_count(path) for path in LOCAL_BACKUP_PATHS])
    count = 0
    progress = Progress(
        TextColumn("[bold blue]hello world", justify="right"),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.1f}%",
        "•",
        TimeRemainingColumn(),
    )

    with progress:
        upload_task_id = progress.add_task("Upload")
        progress.update(upload_task_id, total=total_files)

        for path in LOCAL_BACKUP_PATHS:
            for file in glob.glob(f"{path}/**", recursive=True):
                upload_file(upload_task_id, file, folder_id)


except HttpError as e:
    print(f"Error: {e}")
