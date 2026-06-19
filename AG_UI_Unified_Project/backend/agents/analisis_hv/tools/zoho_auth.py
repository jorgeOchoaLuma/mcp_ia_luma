"""
Manejo de OAuth token de Zoho.
Un solo token sirve para Recruit API y Sheet API
siempre que el scope incluya ambos.

Scope necesario al generar el refresh_token:
  ZohoRecruit.modules.all,
  ZohoRecruit.modules.attachments.all,
  ZohoSheet.dataAPI.UPDATE,
  ZohoSheet.dataAPI.READ
"""
import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

_cache = {"access_token": None, "expires_at": 0}


def get_access_token() -> str:
    now = time.time()
    if _cache["access_token"] and now < _cache["expires_at"] - 60:
        return _cache["access_token"]

    res = requests.post(
        "https://accounts.zoho.com/oauth/v2/token",
        params={
            "grant_type": "refresh_token",
            "refresh_token": os.getenv("ZOHO_REFRESH_TOKEN"),
            "client_id": os.getenv("ZOHO_CLIENT_ID"),
            "client_secret": os.getenv("ZOHO_CLIENT_SECRET"),
        },
    )
    res.raise_for_status()
    data = res.json()
    _cache["access_token"] = data["access_token"]
    _cache["expires_at"] = now + data.get("expires_in", 3600)
    return _cache["access_token"]


def get_headers() -> dict:
    return {"Authorization": f"Zoho-oauthtoken {get_access_token()}"}