#!/usr/bin/env python3
"""
AlphaQuant MCP Server
Servidor MCP (Model Context Protocol) ligero y con cero dependencias externas.
Permite a Claude Desktop, Cursor, Windsurf y agentes autónomos consumir
datos cuantitativos de mercado de SPX en tiempo real.
"""

import sys
import json
import urllib.request
import urllib.error

API_BASE = "https://end-points.vercel.app/v1/market"
USER_AGENT = "AlphaQuant-MCP-Agent/1.0"

TOOLS = [
    {
        "name": "get_market_summary",
        "description": "Obtiene el resumen cuantitativo completo de SPX en un solo payload: precio spot, Expected Move (0DTE), bandas de volatilidad, VIX, tendencia, centroide y precio objetivo de cierre.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
    },
    {
        "name": "get_expected_move",
        "description": "Obtiene el rango de volatilidad y recorrido esperado para la sesión (0DTE/SPX), incluyendo el límite superior (upper_bound) y límite inferior (lower_bound).",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
    },
    {
        "name": "get_market_regime",
        "description": "Obtiene el nivel de VIX, régimen de tendencia actual y sesgo direccional pronosticado (UP, DOWN, SIDEWAYS) con su porcentaje de confianza.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
    },
    {
        "name": "get_reversion_levels",
        "description": "Obtiene los niveles cuantitativos de reversión a la media: centroide de equilibrio, precio objetivo de cierre (target_close) y desviaciones en tiempo real.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
    }
]

def fetch_endpoint(path: str) -> dict:
    url = f"{API_BASE}{path}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {"error": f"Error conectando a AlphaQuant API: {str(exc)}"}

def handle_request(req: dict) -> dict:
    req_id = req.get("id")
    method = req.get("method")
    params = req.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "AlphaQuant-MCP",
                    "version": "1.0.0"
                }
            }
        }

    elif method == "notifications/initialized":
        return None

    elif method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": TOOLS
            }
        }

    elif method == "tools/call":
        tool_name = params.get("name")
        endpoint_map = {
            "get_market_summary": "/summary",
            "get_expected_move": "/expected-move",
            "get_market_regime": "/regime",
            "get_reversion_levels": "/levels"
        }
        
        path = endpoint_map.get(tool_name)
        if not path:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Herramienta desconocida: {tool_name}"}
            }

        data = fetch_endpoint(path)
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(data, indent=2, ensure_ascii=False)
                    }
                ]
            }
        }

    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Método no soportado: {method}"}
        }

def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            res = handle_request(req)
            if res is not None:
                sys.stdout.write(json.dumps(res) + "\n")
                sys.stdout.flush()
        except Exception as e:
            err_res = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
            }
            sys.stdout.write(json.dumps(err_res) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
