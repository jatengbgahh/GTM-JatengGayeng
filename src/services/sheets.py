import asyncio
import logging
import gspread
from google.oauth2.service_account import Credentials
import os
import datetime

from src.config import GOOGLE_SHEET_URL

logger = logging.getLogger(__name__)

def _sync_save_to_gsheet(data: dict) -> dict:
    """Blocking function to save to google sheets, to be called in a thread.
    
    Returns:
        dict: {"success": True} on success, {"success": False, "error": str} on failure.
    """
    if not GOOGLE_SHEET_URL:
        msg = "GOOGLE_SHEET_URL belum diatur di file .env."
        logger.warning(msg)
        return {"success": False, "error": msg}

    credentials_file = "credentials.json"
    if not os.path.exists(credentials_file):
        msg = f"File credentials Google Sheets '{credentials_file}' tidak ditemukan."
        logger.warning(msg)
        return {"success": False, "error": msg}

    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_file(credentials_file, scopes=scopes)
        client = gspread.authorize(creds)
        
        sheet = client.open_by_url(GOOGLE_SHEET_URL).sheet1
        
        # Prepare row data
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [
            now, # Timestamp
            data.get("telegram_user_id"),
            data.get("telegram_username", ""),
            data.get("event_name"),
            data.get("branch"),
            data.get("wok"),
            data.get("location", {}).get("latitude"),
            data.get("location", {}).get("longitude")
        ]
        
        sheet.append_row(row)
        logger.info(f"Data saved to Google Sheets: {data.get('event_name')}")
        return {"success": True}
        
    except Exception as e:
        logger.error(f"Error saving to Google Sheets: {e}")
        return {"success": False, "error": str(e)}

async def save_to_gsheet(data: dict) -> dict:
    """Saves the event data to Google Sheets asynchronously."""
    return await asyncio.to_thread(_sync_save_to_gsheet, data)
