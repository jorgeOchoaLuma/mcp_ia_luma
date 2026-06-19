import base64
import json
import os
import tempfile
from pathlib import Path


def setup_gcp_credentials(base_dir: Path | None = None) -> None:
    """Resolve GCP credentials from base64 env, file path, or ADC."""
    creds_b64 = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_BASE64")
    if creds_b64:
        creds_json = base64.b64decode(creds_b64).decode("utf-8")
        json.loads(creds_json)
        fd, path = tempfile.mkstemp(suffix=".json", prefix="gcp-creds-")
        with os.fdopen(fd, "w") as f:
            f.write(creds_json)
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path
        return

    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path:
        return

    if os.path.isabs(creds_path):
        return

    root = base_dir or Path.cwd()
    resolved = (root / creds_path).resolve()
    if resolved.exists():
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(resolved)


def get_service_account_email() -> str | None:
    """Return client_email from active credentials file (for IAM debugging)."""
    creds_b64 = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_BASE64")
    if creds_b64:
        try:
            data = json.loads(base64.b64decode(creds_b64).decode("utf-8"))
            return data.get("client_email")
        except Exception:
            return None

    creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path or not os.path.isfile(creds_path):
        return None
    try:
        with open(creds_path, encoding="utf-8") as f:
            return json.load(f).get("client_email")
    except Exception:
        return None
