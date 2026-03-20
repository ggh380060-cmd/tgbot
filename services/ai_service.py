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
    import asyncio

    seed = random.randint(1, 999999)
    encoded = urllib.parse.quote(prompt)

    # Разные модели Pollinations
    urls = [
        f"https://image.pollinations.ai/prompt/{encoded}?model=flux-schnell&seed={seed}&nologo=true&width=1024&height=1024",
        f"https://image.pollinations.ai/prompt/{encoded}?model=flux&seed={seed}&nologo=true&width=1024&height=1024",
        f"https://image.pollinations.ai/prompt/{encoded}?model=turbo&seed={seed}&nologo=true&width=512&height=512",
    ]

    for i, url in enumerate(urls):
        try:
            log.info(f"Попытка {i+1}/3...")
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        if len(data) > 5000:
                            log.info(f"Готово: {len(data)} байт")
                            return data
                    log.warning(f"Статус {resp.status}")
        except Exception as e:
            log.warning(f"Попытка {i+1} ошибка: {e}")
        await asyncio.sleep(3)

    raise Exception("Не удалось сгенерировать картинку.")

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