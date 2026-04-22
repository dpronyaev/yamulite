"""Yandex OAuth device-flow and token storage."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import requests

try:
    import keyring
    _HAS_KEYRING = True
except Exception:
    _HAS_KEYRING = False

# Public client credentials of the Yandex Music mobile app — used by the
# yandex-music-api ecosystem. Not a secret in any meaningful sense.
CLIENT_ID = "23cabbbdc6cd418abb4b39c32c41195d"
CLIENT_SECRET = "53bc75238f0c4d08a118e51fe9203300"

SERVICE_NAME = "yamulite"
TOKEN_KEY = "oauth_token"

TOKEN_FILE = Path.home() / ".yamulite" / "token.json"


@dataclass
class DeviceCode:
    device_code: str
    user_code: str
    verification_url: str
    interval: int
    expires_in: int


def request_device_code() -> DeviceCode:
    r = requests.post(
        "https://oauth.yandex.ru/device/code",
        data={"client_id": CLIENT_ID},
        timeout=15,
    )
    r.raise_for_status()
    data = r.json()
    return DeviceCode(
        device_code=data["device_code"],
        user_code=data["user_code"],
        verification_url=data.get("verification_url", "https://ya.ru/device"),
        interval=int(data.get("interval", 5)),
        expires_in=int(data.get("expires_in", 600)),
    )


def poll_token(device_code: str) -> Optional[str]:
    """One poll attempt. Returns token on success, None if still pending,
    raises RuntimeError on terminal error."""
    r = requests.post(
        "https://oauth.yandex.ru/token",
        data={
            "grant_type": "device_code",
            "code": device_code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        },
        timeout=15,
    )
    if r.status_code == 200:
        return r.json()["access_token"]
    try:
        err = r.json().get("error", "")
    except Exception:
        err = r.text
    if err in ("authorization_pending", "slow_down"):
        return None
    raise RuntimeError(f"OAuth error: {err}")


def wait_for_token(device: DeviceCode, stop_flag=None) -> str:
    """Blocking polling loop. `stop_flag` is an optional callable -> bool."""
    deadline = time.time() + device.expires_in
    interval = device.interval
    while time.time() < deadline:
        if stop_flag and stop_flag():
            raise RuntimeError("cancelled")
        token = poll_token(device.device_code)
        if token:
            return token
        time.sleep(interval)
    raise RuntimeError("device code expired")


def save_token(token: str) -> None:
    if _HAS_KEYRING:
        try:
            keyring.set_password(SERVICE_NAME, TOKEN_KEY, token)
            return
        except Exception:
            pass
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    TOKEN_FILE.write_text(json.dumps({"token": token}))
    os.chmod(TOKEN_FILE, 0o600)


def load_token() -> Optional[str]:
    if _HAS_KEYRING:
        try:
            t = keyring.get_password(SERVICE_NAME, TOKEN_KEY)
            if t:
                return t
        except Exception:
            pass
    if TOKEN_FILE.exists():
        try:
            return json.loads(TOKEN_FILE.read_text()).get("token")
        except Exception:
            return None
    return None


def clear_token() -> None:
    if _HAS_KEYRING:
        try:
            keyring.delete_password(SERVICE_NAME, TOKEN_KEY)
        except Exception:
            pass
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
