import logging
import httpx
import urllib.parse

log = logging.getLogger("image_service")

async def generate_image(prompt: str, width: int = 1024, height: int = 1024) -> bytes | None:
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&nologo=true&seed={__import__('random').randint(1,99999)}"
    log.info(f"Генерация картинки: {prompt[:60]}...")
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                r = await client.get(url, follow_redirects=True)
                if r.status_code == 200:
                    log.info("✅ Картинка готова")
                    return r.content
                log.warning(f"❌ Ошибка Pollinations: статус {r.status_code}, попытка {attempt+1}/3")
        except httpx.TimeoutException:
            log.error(f"❌ Таймаут, попытка {attempt+1}/3")
        except Exception as e:
            log.error(f"❌ Ошибка: {e}, попытка {attempt+1}/3")
    return None
