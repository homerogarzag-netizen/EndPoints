import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import httpx
from api.config import SUPABASE_URL, SUPABASE_KEY, DEBUG

logger = logging.getLogger("db")

# Datos de respaldo para pruebas locales o cuando no hay registros aún
MOCK_MARKET_DATA = {
    "symbol": "SPX",
    "price": 5850.25,
    "expected_move": 25.50,
    "vix": 16.20,
    "trend_status": "bullish_expansion",
    "centroid": 5842.00,
    "target_close": 5865.00,
    "predicted_direction": "UP",
    "predicted_strength": 0.82,
    "created_at": datetime.now(timezone.utc).isoformat()
}

async def get_latest_market_data() -> Dict[str, Any]:
    """
    Obtiene el registro más reciente de la tabla 'market_logs' en Supabase.
    Si Supabase no está configurado o falla temporalmente, devuelve datos de respaldo.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        if DEBUG:
            logger.info("Supabase no configurado, utilizando datos mock para desarrollo.")
        return MOCK_MARKET_DATA.copy()

    url = f"{SUPABASE_URL}/rest/v1/market_logs"
    params = {
        "select": "*",
        "order": "created_at.desc",
        "limit": 1
    }
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Accept": "application/json"
    }

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if data and isinstance(data, list) and len(data) > 0:
                    row = data[0]
                    return {
                        "symbol": row.get("symbol", "SPX"),
                        "price": float(row.get("price", 0.0)),
                        "expected_move": float(row.get("expected_move", 0.0)),
                        "vix": float(row.get("vix", 0.0)),
                        "trend_status": str(row.get("trend_status", "neutral")),
                        "centroid": float(row.get("centroid", 0.0)),
                        "target_close": float(row.get("target_close", 0.0)),
                        "predicted_direction": str(row.get("predicted_direction", "SIDEWAYS")),
                        "predicted_strength": float(row.get("predicted_strength", 0.0)),
                        "created_at": row.get("created_at") or datetime.now(timezone.utc).isoformat()
                    }
                else:
                    if DEBUG:
                        logger.warning("market_logs está vacía. Retornando datos mock.")
                    return MOCK_MARKET_DATA.copy()
            else:
                if DEBUG:
                    logger.error(f"Error consultando market_logs: {resp.status_code} - {resp.text}")
                return MOCK_MARKET_DATA.copy()
    except Exception as exc:
        if DEBUG:
            logger.error(f"Excepción al conectar con Supabase: {exc}")
        return MOCK_MARKET_DATA.copy()

async def check_database_health() -> bool:
    """Verifica si las credenciales de Supabase están configuradas y responden."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return False
    try:
        url = f"{SUPABASE_URL}/rest/v1/market_logs"
        params = {"select": "id", "limit": 1}
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}"
        }
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            return resp.status_code in [200, 206]
    except Exception:
        return False
