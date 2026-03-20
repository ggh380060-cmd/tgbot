import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    # Telegram
    BOT_TOKEN: str

    # Groq (бесплатный ИИ)
    GROQ_API_KEY: str
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Картинки — Pollinations.AI (вообще без ключей)
    IMAGE_WIDTH: int = 1024
    IMAGE_HEIGHT: int = 1024

    # Лимиты
    MAX_HISTORY: int = 20
    MAX_CHAT_PER_DAY: int = 100
    MAX_IMAGE_PER_DAY: int = 20

    # Admins
    ADMIN_IDS: list = field(default_factory=list)

    def __post_init__(self):
        if not self.BOT_TOKEN:
            raise ValueError("❌ BOT_TOKEN не задан в .env файле!")
        if not self.GROQ_API_KEY:
            raise ValueError("❌ GROQ_API_KEY не задан в .env файле!")

        raw = os.getenv("ADMIN_IDS", "")
        self.ADMIN_IDS = [int(x.strip()) for x in raw.split(",") if x.strip().isdigit()]


config = Config(
    BOT_TOKEN=os.getenv("BOT_TOKEN", ""),
    GROQ_API_KEY=os.getenv("GROQ_API_KEY", ""),
    GROQ_MODEL=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
    IMAGE_WIDTH=int(os.getenv("IMAGE_WIDTH", "1024")),
    IMAGE_HEIGHT=int(os.getenv("IMAGE_HEIGHT", "1024")),
    MAX_HISTORY=int(os.getenv("MAX_HISTORY", "20")),
    MAX_CHAT_PER_DAY=int(os.getenv("MAX_CHAT_PER_DAY", "100")),
    MAX_IMAGE_PER_DAY=int(os.getenv("MAX_IMAGE_PER_DAY", "20")),
)
