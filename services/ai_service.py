import logging
import base64
import urllib.parse
import asyncio
import aiohttp
from groq import AsyncGroq
from config import config

log = logging.getLogger("ai_service")
groq_client = AsyncGroq(api_key=config.GROQ_API_KEY)

SYSTEM_PROMPT = "You are a helpful AI assistant. Reply in the language the user writes in. Be concise. No markdown."

async def chat(messages: list) -> str:
    full = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
    resp = await groq_client.chat.completions.create(
        model=config.GROQ_MODEL,
        messages=full,
        max_tokens=2048,
        temperature=0.8,
    )
    answer = resp.choices[0].message.content
    log.info(f"Groq: {len(answer)} chars")
    return answer

async def analyze_photo(image_bytes: bytes, question: str = None) -> str:
    if not question:
        question = "Describe this photo in detail in Russian."
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

async def generate_image(prompt: str) -> bytes:
    import random
    seed = random.randint(1, 999999)
    encoded = urllib.parse.quote(prompt)
    urls = [
        f"https://image.pollinations.ai/prompt/{encoded}?model=flux-schnell&seed={seed}&nologo=true&width=1024&height=1024",
        f"https://image.pollinations.ai/prompt/{encoded}?model=flux&seed={seed}&nologo=true&width=1024&height=1024",
        f"https://image.pollinations.ai/prompt/{encoded}?model=turbo&seed={seed}&nologo=true&width=512&height=512",
    ]
    for i, url in enumerate(urls):
        try:
            log.info(f"Attempt {i+1}/3")
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        if len(data) > 5000:
                            log.info(f"Image ready: {len(data)} bytes")
                            return data
                    log.warning(f"Status {resp.status}")
        except Exception as e:
            log.warning(f"Attempt {i+1} error: {e}")
        await asyncio.sleep(3)
    raise Exception("Failed to generate image.")

async def improve_image_prompt(user_prompt: str) -> str:
    try:
        resp = await groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "Improve this image prompt for AI generation. Translate to English if needed. Add artistic details. Reply ONLY with the prompt. Max 100 words."},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=150,
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return user_prompt