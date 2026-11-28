"""Generate and persist a local LiteLLM Proxy master key."""

import secrets
from pathlib import Path

from dotenv import dotenv_values, set_key

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
KEY_NAME = "LITELLM_MASTER_KEY"


def main() -> None:
    if not ENV_PATH.is_file():
        raise SystemExit(
            ".env file not found. Copy .env.example to .env first."
        )

    existing_key = dotenv_values(ENV_PATH).get(KEY_NAME)

    if existing_key:
        print("LiteLLM master key already configured. No changes made.")
        return

    # LiteLLM keys start with "sk-"; 32 random bytes as hex give a 64-character secret.
    key = "sk-" + secrets.token_hex(32)

    success, _, _ = set_key(
        ENV_PATH,
        KEY_NAME,
        key,
        quote_mode="never",
    )

    if not success:
        raise RuntimeError("Failed to save LiteLLM master key.")

    print("LiteLLM master key generated and saved to .env.")


if __name__ == "__main__":
    main()
