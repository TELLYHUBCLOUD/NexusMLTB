"""
Google Drive upload helper.
Supports service account (SA) or OAuth token.pickle.
"""
import os
import pickle
from pathlib import Path

try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    GDRIVE_AVAILABLE = True
except ImportError:
    GDRIVE_AVAILABLE = False

from config import Config


SCOPES = ["https://www.googleapis.com/auth/drive"]


def _get_credentials():
    creds = None
    token_path = Config.TOKEN_PICKLE
    if os.path.exists(token_path):
        with open(token_path, "rb") as f:
            creds = pickle.load(f)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds


def _build_service():
    creds = _get_credentials()
    if not creds:
        raise RuntimeError("Google Drive credentials not configured.")
    return build("drive", "v3", credentials=creds, cache_discovery=False)


async def upload_to_gdrive(file_path: str, folder_id: str = None) -> dict | None:
    """Upload file to Google Drive. Returns file metadata dict or None."""
    if not GDRIVE_AVAILABLE:
        return None

    import asyncio
    loop = asyncio.get_event_loop()

    def _upload():
        service = _build_service()
        name    = Path(file_path).name
        meta    = {"name": name}
        if folder_id or Config.GDRIVE_FOLDER_ID:
            meta["parents"] = [folder_id or Config.GDRIVE_FOLDER_ID]

        media = MediaFileUpload(file_path, resumable=True)
        file  = service.files().create(body=meta, media_body=media, fields="id,name,webViewLink").execute()
        return file

    try:
        return await loop.run_in_executor(None, _upload)
    except Exception as e:
        print(f"GDrive upload error: {e}")
        return None


async def download_from_gdrive(file_id: str, dest_dir: str) -> str | None:
    """Download a file from Google Drive by file_id. Returns path or None."""
    if not GDRIVE_AVAILABLE:
        return None

    import io
    import asyncio
    from googleapiclient.http import MediaIoBaseDownload

    loop = asyncio.get_event_loop()

    def _download():
        service  = _build_service()
        meta     = service.files().get(fileId=file_id, fields="name").execute()
        name     = meta.get("name", file_id)
        out_path = os.path.join(dest_dir, name)
        request  = service.files().get_media(fileId=file_id)
        with open(out_path, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
        return out_path

    try:
        return await loop.run_in_executor(None, _download)
    except Exception as e:
        print(f"GDrive download error: {e}")
        return None
