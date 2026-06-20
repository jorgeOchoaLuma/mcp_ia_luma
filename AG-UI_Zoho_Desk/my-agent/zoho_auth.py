"""OAuth Zoho — token para MCP Desk (mismo flujo que Recruit/Sheet)."""
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

_cache = {"access_token": None, "expires_at": 0}


def get_access_token() -> str:
    token = os.getenv("ZOHO_ACCESS_TOKEN")
    if token:
        return token

    now = time.time()
    if _cache["access_token"] and now < _cache["expires_at"] - 60:
        return _cache["access_token"]

    refresh = os.getenv("ZOHO_REFRESH_TOKEN")
    client_id = os.getenv("ZOHO_CLIENT_ID")
    client_secret = os.getenv("ZOHO_CLIENT_SECRET")
    if not all([refresh, client_id, client_secret]):
        raise RuntimeError(
            "Faltan ZOHO_REFRESH_TOKEN, ZOHO_CLIENT_ID o ZOHO_CLIENT_SECRET para MCP Desk"
        )

    res = requests.post(
        "https://accounts.zoho.com/oauth/v2/token",
        params={
            "grant_type": "refresh_token",
            "refresh_token": refresh,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=30,
    )
    res.raise_for_status()
    data = res.json()
    _cache["access_token"] = data["access_token"]
    _cache["expires_at"] = now + data.get("expires_in", 3600)
    return _cache["access_token"]


def mcp_auth_headers() -> dict[str, str]:
    return {"Authorization": f"Zoho-oauthtoken {get_access_token()}"}
