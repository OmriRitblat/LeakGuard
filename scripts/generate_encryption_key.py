
"""Generate and persist a local AES-256 encryption key."""

import base64
import secrets
from pathlib import Path

from dotenv import dotenv_values, set_key

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
KEY_NAME = "LEAKGUARD_ENCRYPTION_KEY"


def main() -> None:
    if not ENV_PATH.is_file():
        raise SystemExit(
            ".env file not found. Copy .env.example to .env first."
        )

    existing_key = dotenv_values(ENV_PATH).get(KEY_NAME)

    if existing_key:
        print("Encryption key already configured. No changes made.")
        return

    key = secrets.token_bytes(32)
    encoded_key = base64.b64encode(key).decode("ascii")

    success, _, _ = set_key(
        ENV_PATH,
        KEY_NAME,
        encoded_key,
        quote_mode="never",
    )

    if not success:
        raise RuntimeError("Failed to save encryption key.")

    print("Encryption key generated and saved to .env.")


if __name__ == "__main__":
    main()
