import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    api_key: str
    account_id: str
    api_base_url: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        missing = [name for name in ("WIX_API_KEY", "WIX_ACCOUNT_ID") if not os.getenv(name)]
        if missing:
            raise RuntimeError(f"Missing {', '.join(missing)}. Copy .env.example to .env and fill it in.")
        return cls(
            api_key=os.environ["WIX_API_KEY"],
            account_id=os.environ["WIX_ACCOUNT_ID"],
            api_base_url=os.getenv("WIX_API_BASE_URL", "https://www.wixapis.com"),
        )
