"""
Все ИИ-сервисы — только бесплатные:

  - Groq API  → чат (Llama 3.3, бесплатно 14 400 req/день)
  - Groq API  → анализ фото (llama-4-scout, бесплатно)
  - Pollinations.AI → генерация картинок (вообще без ключей и без лимитов)
"""

import logging
import base64
import urllib.parse
import aiohttp
from groq import AsyncGroq
import asyncio
from config import config

log = logging.getLogger("ai_service")

# Один клиент Groq на всё приложение
groq_client = AsyncGroq(api_key=config.GROQ_API_KEY)

SYSTEM_PROMPT = """Ты умный и полезный ИИ-ассистент в Telegram.
Отвечай на том языке, на котором пишет пользователь.
Будь конкретным. Не используй markdown разметку — только обычный текст.
Помни контекст нашего разговора."""


# ══════════════════════════════════════════════════════════════
#  ЧАТ — Groq (Llama 3.3)
# ══════════════════════════════════════════════════════════════

async def chat(messages: list[dict]) -> str:
    """
    Отправляет историю в Groq и возвращает ответ.
    messages = [{"role": "user"/"assistant", "content": "текст"}, ...]
    """
    try:
        full = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

        resp = await groq_client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=full,
            max_tokens=2048,
            temperature=0.8,
        )

        answer = resp.choices[0].message.content
        tokens = resp.usage.total_tokens
        log.info(f"Groq ответ: {len(answer)} символов, {tokens} токенов")
        return answer

    except Exception as e:
        log.error(f"Ошибка Groq chat: {e}")
        raise


# ══════════════════════════════════════════════════════════════
#  АНАЛИЗ ФОТО — Groq Vision (llama-4-scout)
# ══════════════════════════════════════════════════════════════

async def analyze_photo(image_bytes: bytes, question: str = None) -> str:
    """
    Анализирует фото через Groq Vision.
    Бесплатно, модель llama-4-scout поддерживает картинки.
    """
    if not question:
        question = "Подробно опиши что изображено на этом фото на русском языке."

    try:
        b64 = base64.b64encode(image_bytes).decode("utf-8")

        resp = await groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64}"
                            },
                        },
                        {"type": "text", "text": question},
                    ],
                }
            ],
            max_tokens=1024,
        )

        answer = resp.choices[0].message.content
        log.info(f"Vision ответ: {len(answer)} символов")
        return answer

    except Exception as e:
        log.error(f"Ошибка Groq Vision: {e}")
        raise


# ══════════════════════════════════════════════════════════════
#  ГЕНЕРАЦИЯ КАРТИНОК — Pollinations.AI (полностью бесплатно)
# ══════════════════════════════════════════════════════════════

async def generate_image(prompt: str) -> bytes:
    """
    Генерирует картинку через Hugging Face (бесплатно).
    Модель: FLUX.1-schnell — быстрая и качественная.
    """
    import asyncio
    import json

    api_url = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
    headers = {"Authorization": f"Bearer {config.HF_TOKEN}"}
    payload = {"inputs": prompt}

    for attempt in range(3):
        try:
            log.info(f"HF попытка {attempt+1}/3: {prompt[:60]}...")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    api_url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as resp:

                    if resp.status == 200:
                        data = await resp.read()
                        if len(data) > 5000:
                            log.info(f"✅ Картинка готова: {len(data)} байт")
                            return data

                    elif resp.status == 503:
                        # Модель загружается — подождём
                        text = await resp.text()
                        log.warning(f"Модель загружается, ждём 10 сек...")
                        await asyncio.sleep(10)
                        continue

                    else:
                        text = await resp.text()
                        log.warning(f"HF статус {resp.status}: {text[:100]}")

        except asyncio.TimeoutError:
            log.warning(f"Попытка {attempt+1} — таймаут")
        except Exception as e:
            log.warning(f"Попытка {attempt+1} — ошибка: {e}")

        if attempt < 2:
            await asyncio.sleep(5)

    raise Exception("Не удалось сгенерировать картинку. Попробуй позже.")
══════════════════════════════════════════════════════════════
#  УЛУЧШЕНИЕ ПРОМПТА для картинок
# ══════════════════════════════════════════════════════════════

async def improve_image_prompt(user_prompt: str) -> str:
    """
    Улучшает описание картинки через Groq (бесплатно).
    Переводит на английский и добавляет детали.
    """
    try:
        resp = await groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",  # быстрая и бесплатная
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert at writing image generation prompts. "
                        "Take the user's description, translate it to English if needed, "
                        "and enhance it with artistic details (style, lighting, mood). "
                        "Reply ONLY with the improved prompt, no explanations. Max 100 words."
                    ),
                },
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=150,
            temperature=0.7,
        )
        improved = resp.choices[0].message.content.strip()
        log.info(f"Промпт улучшен: '{user_prompt[:30]}' → '{improved[:40]}...'")
        return improved
    except Exception:
        # Если не вышло — используем оригинал
        return user_prompt
