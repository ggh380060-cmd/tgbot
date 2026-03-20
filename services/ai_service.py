import logging
import base64
import urllib.parse
import asyncio
import aiohttp
import random
from groq import AsyncGroq
from config import config

log = logging.getLogger("ai_service")
groq_client = AsyncGroq(api_key=config.GROQ_API_KEY)

SYSTEM_PROMPT = """Ты умный, дружелюбный и остроумный AI-ассистент. 
Отвечай на языке пользователя (русский или другой).
Будь полезным, конкретным и по делу. 
Можешь шутить и быть неформальным, но всегда отвечай по существу.
Если не знаешь ответа — честно скажи об этом.
Не используй markdown разметку (никаких **, ## и т.д.)."""

async def chat(messages: list) -> str:
    full = [{"role": "system", "content": SYSTEM_PROMPT}] + messages[-20:]
    resp = await groq_client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=full,
        max_tokens=2048,
        temperature=0.9,
    )
    answer = resp.choices[0].message.content
    log.info(f"Groq ответ: {len(answer)} символов")
    return answer

async def analyze_photo(image_bytes: bytes, question: str = None) -> str:
    if not question:
        question = "Подробно опиши что изображено на фото. Отвечай на русском."
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    resp = await groq_client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            {"type": "text", "text": question},
        ]}],
        max_tokens=1024,
    )
    return resp.choices[0].message.content

async def improve_image_prompt(user_prompt: str) -> str:
    try:
        resp = await groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Translate to English if needed and improve this image generation prompt. Add visual details, lighting, style. Reply ONLY with the improved prompt, max 80 words."},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=120,
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return user_prompt

async def generate_image(prompt: str) -> bytes:
    seed = random.randint(1, 999999)
    encoded = urllib.parse.quote(prompt, safe="")

    urls = [
        f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={seed}",
        f"https://pollinations.ai/p/{encoded}?width=1024&height=1024&seed={seed}",
        f"https://image.pollinations.ai/prompt/{encoded}?width=512&height=512&nologo=true&seed={seed}",
    ]

    async with aiohttp.ClientSession() as session:
        for i, url in enumerate(urls):
            try:
                log.info(f"Генерация картинки попытка {i+1}/3")
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=90), allow_redirects=True) as resp:
                    content_type = resp.headers.get("content-type", "")
                    if resp.status == 200 and "image" in content_type:
                        data = await resp.read()
                        if len(data) > 10000:
                            log.info(f"Картинка готова: {len(data)} байт")
                            return data
                    log.warning(f"Попытка {i+1}: статус {resp.status}, тип {content_type}")
            except Exception as e:
                log.warning(f"Попытка {i+1} ошибка: {e}")
            await asyncio.sleep(2)

    raise Exception("Не удалось сгенерировать картинку.")
