import logging
import httpx
import urllib.parse
import random
from groq import AsyncGroq
import os

log = logging.getLogger("image_service")

async def translate_to_english(prompt: str) -> str:
    try:
        client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
        response = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{
                "role": "user",
                "content": f"Translate this image description to English. Reply with ONLY the translation, nothing else: {prompt}"
            }],
            max_tokens=200,
        )
        result = response.choices[0].message.content.strip()
        log.info(f"Перевод: '{prompt}' -> '{result}'")
        return result
    except Exception as e:
        log.error(f"Ошибка перевода: {e}")
        return prompt

async def generate_image(prompt: str, width: int = 1024, height: int = 1024) -> bytes | None:
    english_prompt = await translate_to_english(prompt)
    encoded = urllib.parse.quote(english_prompt, safe="")
    seed = random.randint(1, 999999)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true&seed={seed}&model=flux"
    log.info(f"Генерация: '{english_prompt[:60]}...'")

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                r = await client.get(url, follow_redirects=True)
                if r.status_code == 200 and len(r.content) > 1000:
                    log.info(f"Картинка готова, размер: {len(r.content)} байт")
                    return r.content
                log.warning(f"Pollinations статус {r.status_code}, попытка {attempt+1}/3")
        except httpx.TimeoutException:
            log.error(f"Таймаут, попытка {attempt+1}/3")
        except Exception as e:
            log.error(f"Ошибка: {e}, попытка {attempt+1}/3")
    return None
