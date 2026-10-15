import logging
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import httpx
from api.config import SUPABASE_URL, SUPABASE_KEY, DEBUG

logger = logging.getLogger("telemetry")
if DEBUG:
    logging.basicConfig(level=logging.INFO)

def classify_user_agent(user_agent: str) -> str:
    """Clasifica la huella digital del visitante a partir del User-Agent."""
    ua = (user_agent or "").lower()
    if not ua:
        return "unknown"

    # Detección de Agentes de IA y MCP
    ai_signatures = [
        "claude-code", "antigravity", "cursor", "langchain",
        "crewai", "autogpt", "openai", "mcp", "agent",
        "copilot", "chatgpt", "lobe", "llamaindex", "smithery", "arcade"
    ]
    if any(sig in ua for sig in ai_signatures):
        return "ai_agent"

    # Clientes de código / librerías
    code_signatures = ["python", "requests", "httpx", "aiohttp", "urllib", "go-http", "axios", "node-fetch"]
    if any(sig in ua for sig in code_signatures):
        return "python_client"

    # Herramientas de terminal
    cli_signatures = ["curl", "wget", "httpie"]
    if any(sig in ua for sig in cli_signatures):
        return "cli_tool"

    # Navegadores convencionales
    browser_signatures = ["mozilla", "chrome", "safari", "edge", "firefox"]
    if any(sig in ua for sig in browser_signatures):
        return "browser"

    return "other"

async def record_telemetry(
    endpoint: str,
    method: str,
    user_agent: str,
    query_params: Dict[str, Any],
    client_ip: Optional[str],
    response_time_ms: float,
    status_code: int = 200,
    headers: Optional[Dict[str, str]] = None
):
    """
    Registra la telemetría en segundo plano en Supabase.
    Diseñado para ser completamente no bloqueante y tolerante a fallos.
    Si Supabase falla o no está configurado, la API continuará funcionando.
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        return

    # Omitir peticiones automáticas de auto-refresco del dashboard para no ensuciar la métrica
    if headers:
        lower_headers = {str(k).lower(): str(v).lower() for k, v in headers.items()}
        if lower_headers.get("x-internal-dashboard") == "true":
            return
    if str(query_params.get("internal", "")).lower() == "1":
        return

    try:
        caller_type = classify_user_agent(user_agent)
        
        # Anonimizar la IP para privacidad
        ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:16] if client_ip else None

        payload = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "endpoint": endpoint,
            "method": method,
            "user_agent": user_agent[:255] if user_agent else None,
            "caller_type": caller_type,
            "query_params": query_params,
            "ip_hash": ip_hash,
            "status_code": status_code,
            "response_time_ms": round(response_time_ms, 2)
        }

        url = f"{SUPABASE_URL}/rest/v1/telemetria_sonda"
        req_headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }

        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.post(url, json=payload, headers=req_headers)
            if resp.status_code >= 400 and DEBUG:
                logger.warning(f"Error registrando telemetría: {resp.status_code} - {resp.text}")

    except Exception as exc:
        if DEBUG:
            logger.warning(f"Excepción silenciosa en telemetría: {exc}")
