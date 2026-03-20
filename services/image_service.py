import logging
import httpx
import urllib.parse
import random
import os

log = logging.getLogger("image_service")

async def translate_to_english(prompt: str) -> str:
    try:
        api_key = os.getenv("GROQ_API_KEY")
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": "Translate the user's text to English. Reply with ONLY the translation, nothing else."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 100
                }
            )
            translated = r.json()["choices"][0]["message"]["content"].strip()
            log.info(f"Перевод: '{prompt}' -> '{translated}'")
            return translated
    except Exception as e:
        log.error(f"Ошибка перевода: {e}")
        return prompt

async def generate_image(prompt: str, width: int = 1024, height: int = 1024) -> bytes | None:
    prompt = await translate_to_english(prompt)
    encoded = urllib.parse.quote(prompt, safe="")
    seed = random.randint(1, 999999)

    urls = [
        f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true&seed={seed}",
        f"https://pollinations.ai/p/{encoded}?width={width}&height={height}&seed={seed}",
    ]

    async with httpx.AsyncClient(timeout=90.0) as client:
        for url in urls:
            for attempt in range(2):
                try:
                    r = await client.get(url, follow_redirects=True)
                    content_type = r.headers.get("content-type", "")
                    if r.status_code == 200 and "image" in content_type and len(r.content) > 10000:
                        log.info(f"Картинка готова, размер: {len(r.content)} байт")
                        return r.content
                    log.warning(f"Статус {r.status_code}, тип {content_type}, размер {len(r.content)}, попытка {attempt+1}/2")
                except httpx.TimeoutException:
                    log.error(f"Таймаут, попытка {attempt+1}/2")
                except Exception as e:
                    log.error(f"Ошибка: {e}, попытка {attempt+1}/2")

    log.error("Все попытки провалились")
    return None
