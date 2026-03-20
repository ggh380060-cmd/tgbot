"""
Генерация изображений через Pollinations.AI — бесплатно, без ключей.
"""

import logging
import httpx
import urllib.parse

log = logging.getLogger("image_service")

POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}"


async def generate_image(prompt: str, width: int = 1024, height: int = 1024) -> bytes | None:
    """
    Генерирует изображение по текстовому описанию.
    Возвращает bytes картинки или None при ошибке.
    """
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"

    log.info(f"Генерация картинки: {prompt[:60]}...")

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, follow_redirects=True)

            if response.status_code == 200:
                log.info("✅ Картинка успешно сгенерирована")
                return response.content
            else:
                log.warning(f"❌ Ошибка Pollinations: статус {response.status_code}")
                return None

    except httpx.TimeoutException:
        log.error("❌ Таймаут при генерации картинки")
        return None
    except Exception as e:
        log.error(f"❌ Ошибка генерации: {e}")
        return None


async def translate_prompt_to_english(prompt: str) -> str:
    """
    Простой хелпер — Pollinations лучше работает с английским.
    Если промпт на русском — добавляем пометку для лучшего результата.
    Для полноценного перевода можно подключить Groq.
    """
    # Если есть кириллица — возвращаем как есть (Pollinations поддерживает русский)
    return prompt
