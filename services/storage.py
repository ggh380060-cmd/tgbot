"""
Хранение данных в памяти:
  - История диалогов пользователей
  - Счётчики использования (лимиты в день)
"""

import logging
from datetime import date
from collections import defaultdict
from config import config

log = logging.getLogger("storage")


class Storage:
    def __init__(self):
        # { user_id: [{"role": "...", "content": "..."}] }
        self._history: dict[int, list] = defaultdict(list)

        # { user_id: {"date": date, "chats": 0, "images": 0} }
        self._usage: dict[int, dict] = {}

        log.info("Storage запущен (хранение в памяти)")

    # ── История диалога ───────────────────────────────────────

    def add_message(self, user_id: int, role: str, content: str):
        self._history[user_id].append({"role": role, "content": content})
        # Оставляем только последние N*2 сообщений (пары user/assistant)
        limit = config.MAX_HISTORY * 2
        if len(self._history[user_id]) > limit:
            self._history[user_id] = self._history[user_id][-limit:]

    def get_history(self, user_id: int) -> list:
        return list(self._history[user_id])

    def clear_history(self, user_id: int) -> int:
        count = len(self._history[user_id])
        self._history[user_id] = []
        return count

    def history_len(self, user_id: int) -> int:
        return len(self._history[user_id])

    # ── Лимиты ───────────────────────────────────────────────

    def _usage_today(self, user_id: int) -> dict:
        today = date.today()
        u = self._usage.get(user_id)
        if not u or u["date"] != today:
            self._usage[user_id] = {"date": today, "chats": 0, "images": 0}
        return self._usage[user_id]

    def can_chat(self, user_id: int) -> bool:
        if user_id in config.ADMIN_IDS:
            return True
        return self._usage_today(user_id)["chats"] < config.MAX_CHAT_PER_DAY

    def can_image(self, user_id: int) -> bool:
        if user_id in config.ADMIN_IDS:
            return True
        return self._usage_today(user_id)["images"] < config.MAX_IMAGE_PER_DAY

    def inc_chat(self, user_id: int):
        self._usage_today(user_id)["chats"] += 1

    def inc_image(self, user_id: int):
        self._usage_today(user_id)["images"] += 1

    def get_stats(self, user_id: int) -> dict:
        u = self._usage_today(user_id)
        return {
            "chats": u["chats"],
            "chats_max": config.MAX_CHAT_PER_DAY,
            "images": u["images"],
            "images_max": config.MAX_IMAGE_PER_DAY,
            "history": self.history_len(user_id),
        }

    def total_users(self) -> int:
        return len(set(self._history.keys()) | set(self._usage.keys()))


# Глобальный экземпляр
storage = Storage()
