import logging
import base64
import urllib.parse
import asyncio
import aiohttp
from groq import AsyncGroq
from config import config

log = logging.getLogger("ai_service")

groq_client = AsyncGroq(api_key=config.GROQ_API_KEY)

SYSTEM_PROMPT = """Ты умный и полезный ИИ-ассистент в Telegram.
Отвечай на том языке, на котором пишет пользователь.
Будь конкретным. Не используй markdown разметку — только обычный текст.
Помни контекст нашего разговора."""


async def chat(messages: list) -> str:
    full = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
    resp = await groq_client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=full,
        max_tokens=2048,
        temperature=0.8,
    )
    answer = resp.choices[0].message.content
    log.info(f"Groq: {len(answer)} символов")
    return answer


async def analyze_photo(image_bytes: bytes, question: str = None) -> str:
    if not question:
        question = "Подробно опиши что изображено на этом фото на русском языке."
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    resp = await groq_client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                    {"type": "text", "text": question},
                ],
            }
        ],
        max_tokens=1024,
    )
    answer = resp.choices[0].message.content
    log.info(f"Vision: {len(answer)} символов")
    return answer


async def generate_image(prompt: str) -> bytes:
    import random
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
                            log.info(f"Картинка готова: {len(data)} байт")
                            return data
                    elif resp.status == 503:
                        log.warning("Модель загружается, ждём 10 сек...")
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


async def improve_image_prompt(user_prompt: str) -> str:
    try:
        resp = await groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert at writing image generation prompts. "
                        "Translate to English if needed and enhance with artistic details. "
                        "Reply ONLY with the improved prompt. Max 100 words."
                    ),
                },
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=150,
            temperature=0.7,
        )
        improved = resp.choices[0].message.content.strip()
        log.info(f"Промпт улучшен: '{user_prompt[:30]}' -> '{improved[:40]}...'")
        return improved
    except Exception:
        return user_prompt