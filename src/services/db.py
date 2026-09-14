import logging
import aiomysql
from typing import Callable, Awaitable

from src.config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

logger = logging.getLogger(__name__)

async def save_to_mysql(data: dict, sheet_callback: Callable[[dict], Awaitable[dict]] = None) -> dict:
    """Saves the event data to MySQL database asynchronously.
    If sheet_callback is provided, it executes it within the MySQL transaction.
    If sheet_callback fails, MySQL transaction is rolled back.
    
    Returns:
        dict: If sheet_callback is provided, returns {"mysql": dict, "sheets": dict}.
              Otherwise, returns {"success": bool, "error": str}.
    """
    mysql_result = {"success": False, "error": ""}
    sheets_result = {"success": False, "error": ""}
    
    try:
        pool = await aiomysql.create_pool(
            host=DB_HOST,
            port=3306,
            user=DB_USER,
            password=DB_PASSWORD,
            db=DB_NAME,
            autocommit=False
        )
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    query = """
                        INSERT INTO event 
                        (telegram_user_id, telegram_username, nama_event, branch, wok, latitude, longitude)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    values = (
                        data.get("telegram_user_id"),
                        data.get("telegram_username"),
                        data.get("event_name"),
                        data.get("branch"),
                        data.get("wok"),
                        data.get("location", {}).get("latitude"),
                        data.get("location", {}).get("longitude"),
                    )
                    await cur.execute(query, values)
                    mysql_result = {"success": True}
                    
                    if sheet_callback:
                        sheets_result = await sheet_callback(data)
                        if sheets_result.get("success"):
                            await conn.commit()
                            logger.info(f"Data saved to MySQL & Google Sheets: {data.get('event_name')}")
                        else:
                            await conn.rollback()
                            logger.warning(f"Google Sheets failed, rolling back MySQL: {data.get('event_name')}")
                            mysql_result = {"success": False, "error": "Dibatalkan karena Google Sheets gagal"}
                    else:
                        await conn.commit()
                        logger.info(f"Data saved to MySQL: {data.get('event_name')}")
                        
                except Exception as e:
                    await conn.rollback()
                    logger.error(f"Error during MySQL execute/transaction: {e}")
                    mysql_result = {"success": False, "error": str(e)}
                    if sheet_callback:
                        sheets_result = {"success": False, "error": "Tidak dijalankan karena MySQL gagal"}

        pool.close()
        await pool.wait_closed()
        
        if sheet_callback:
            return {"mysql": mysql_result, "sheets": sheets_result}
        else:
            return mysql_result
            
    except Exception as e:
        logger.error(f"Error connecting to MySQL: {e}")
        mysql_result = {"success": False, "error": str(e)}
        if sheet_callback:
            sheets_result = {"success": False, "error": "Tidak dijalankan karena gagal koneksi MySQL"}
            return {"mysql": mysql_result, "sheets": sheets_result}
        return mysql_result
