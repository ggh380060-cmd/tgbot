import logging
import httpx
import urllib.parse
import random

log = logging.getLogger("image_service")

PROMPT_PREFIX = "high quality, detailed, "

async def generate_image(prompt: str, width: int = 1024, height: int = 1024) -> bytes | None:
    # Добавляем английский префикс для лучшей совместимости
    full_prompt = PROMPT_PREFIX + prompt
    encoded = urllib.parse.quote(full_prompt, safe="")
    seed = random.randint(1, 999999)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true&seed={seed}&model=flux"
    log.info(f"Генерация картинки: {prompt[:60]}... URL длина: {len(url)}")

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                r = await client.get(url, follow_redirects=True)
                if r.status_code == 200 and len(r.content) > 1000:
                    log.info(f"Картинка готова, размер: {len(r.content)} байт")
                    return r.content
                log.warning(f"Ошибка Pollinations: статус {r.status_code}, попытка {attempt+1}/3")
        except httpx.TimeoutException:
            log.error(f"Таймаут, попытка {attempt+1}/3")
        except Exception as e:
            log.error(f"Ошибка: {e}, попытка {attempt+1}/3")
    return None
