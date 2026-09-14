import httpx
import logging

logger = logging.getLogger(__name__)

async def get_location_details(lat: float, lon: float) -> dict:
    """
    Fetch reverse geocoding data from OpenStreetMap Nominatim API.
    Returns dictionary with kabupaten_kota, kecamatan, kelurahan_desa.
    """
    url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&addressdetails=1"
    headers = {
        "User-Agent": "GTM-JatengGayeng-TelegramBot/1.0"
    }
    
    result = {
        "kabupaten_kota": "-",
        "kecamatan": "-",
        "kelurahan_desa": "-"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                address = data.get("address", {})
                
                result["kabupaten_kota"] = address.get("city") or address.get("regency") or address.get("county") or address.get("town") or "-"
                result["kecamatan"] = address.get("district") or "-"
                result["kelurahan_desa"] = address.get("village") or address.get("suburb") or address.get("neighbourhood") or "-"
    except Exception as e:
        logger.error(f"Error fetching geocoding data: {e}")
        
    return result
