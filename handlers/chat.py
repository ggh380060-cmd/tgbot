"""
Чат с Llama 3.3 через Groq + анализ фото
"""

import logging
from aiogram import Router, F
from aiogram.types import Message
from services.ai_service import chat, analyze_photo
from services.storage import storage

log = logging.getLogger("chat")
router = Router()


# ── Текстовый чат ─────────────────────────────────────────────

@router.message(F.text & ~F.text.startswith("/"))
async def handle_text(msg: Message):
    user_id = msg.from_user.id
    text = msg.text.strip()

    if not storage.can_chat(user_id):
        await msg.answer(
            "⚠️ Лимит чата на сегодня исчерпан (100 сообщений).\n"
            "Возвращайся завтра — лимит сбросится в полночь 🌙"
        )
        return

    # Показываем что думаем
    wait = await msg.answer("🤔 Думаю...")

    try:
        storage.add_message(user_id, "user", text)
        history = storage.get_history(user_id)

        answer = await chat(history)

        storage.add_message(user_id, "assistant", answer)
        storage.inc_chat(user_id)

        await wait.delete()

        # Telegram лимит = 4096 символов — режем если надо
        for chunk in _split(answer):
            await msg.answer(chunk)

    except Exception as e:
        await wait.delete()
        log.error(f"Ошибка чата user={user_id}: {e}")
        await msg.answer(
            "❌ Что-то пошло не так.\n"
            f"<i>Ошибка: {_friendly_error(e)}</i>"
        )
        # Убираем из истории запрос который не отработал
        history = storage.get_history(user_id)
        if history and history[-1]["role"] == "user":
            storage.clear_history(user_id)
            for item in history[:-1]:
                storage.add_message(user_id, item["role"], item["content"])


# ── Анализ фото ───────────────────────────────────────────────

@router.message(F.photo)
async def handle_photo(msg: Message):
    user_id = msg.from_user.id

    if not storage.can_chat(user_id):
        await msg.answer("⚠️ Дневной лимит исчерпан. Приходи завтра!")
        return

    question = msg.caption or "Подробно опиши что изображено на фото."
    wait = await msg.answer("📸 Анализирую фото...")

    try:
        # Берём самое большое фото
        photo = msg.photo[-1]
        file = await msg.bot.get_file(photo.file_id)
        data = await msg.bot.download_file(file.file_path)
        image_bytes = data.read()

        answer = await analyze_photo(image_bytes, question)
        storage.inc_chat(user_id)

        await wait.delete()
        await msg.answer(f"📸 <b>На фото:</b>\n\n{answer}")

    except Exception as e:
        await wait.delete()
        log.error(f"Ошибка Vision user={user_id}: {e}")
        await msg.answer("❌ Не смог проанализировать фото. Попробуй ещё раз.")


# ── Хелперы ───────────────────────────────────────────────────

def _split(text: str, max_len: int = 4000) -> list[str]:
    """Разбивает длинный текст на части."""
    if len(text) <= max_len:
        return [text]
    parts, buf = [], ""
    for line in text.split("\n"):
        if len(buf) + len(line) + 1 > max_len:
            if buf:
                parts.append(buf)
            buf = line
        else:
            buf = buf + ("\n" if buf else "") + line
    if buf:
        parts.append(buf)
    return parts or [text[:max_len]]


def _friendly_error(e: Exception) -> str:
    s = str(e).lower()
    if "rate_limit" in s:
        return "Слишком много запросов, подожди минуту"
    if "invalid_api_key" in s or "authentication" in s:
        return "Неверный API ключ, сообщи администратору"
    if "timeout" in s or "connection" in s:
        return "Сервис временно недоступен, попробуй позже"
    return "Попробуй ещё раз"
