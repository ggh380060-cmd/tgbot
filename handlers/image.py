"""
Генерация картинок через Pollinations.AI — бесплатно, без ключей.
Команда: /image [описание]
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command
from services.image_service import generate_image

log = logging.getLogger("image")
router = Router()


@router.message(Command("image", "img"))
async def cmd_image(msg: Message):
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await msg.answer(
            "🖼 <b>Напиши описание после команды:</b>\n\n"
            "• <code>/image кот в космосе</code>\n"
            "• <code>/image закат над морем</code>\n"
            "• <code>/image футуристический город ночью</code>"
        )
        return

    prompt = parts[1].strip()
    wait = await msg.answer(f"🎨 Рисую: «{prompt[:50]}»\nОбычно 10–25 секунд...")

    try:
        image_bytes = await generate_image(prompt)
        await wait.delete()
        photo = BufferedInputFile(image_bytes, filename="image.png")
        await msg.answer_photo(
            photo=photo,
            caption=f"🖼 Готово!\n📝 Запрос: <i>{prompt}</i>",
        )
    except Exception as e:
        await wait.delete()
        log.error(f"Ошибка генерации: {e}")
        await msg.answer("❌ Не удалось нарисовать. Попробуй ещё раз.")


@router.message(F.text.lower().startswith("нарисуй"))
async def natural_draw(msg: Message):
    prompt = msg.text.split(maxsplit=1)
    prompt = prompt[1].strip() if len(prompt) > 1 else ""
    if not prompt:
        await msg.answer("Что нарисовать? Напиши описание после слова «нарисуй».")
        return

    wait = await msg.answer(f"🎨 Рисую: «{prompt[:50]}»\nОбычно 10–25 секунд...")
    try:
        image_bytes = await generate_image(prompt)
        await wait.delete()
        photo = BufferedInputFile(image_bytes, filename="image.png")
        await msg.answer_photo(photo=photo, caption=f"🖼 Готово!\n📝 Запрос: <i>{prompt}</i>")
    except Exception as e:
        await wait.delete()
        log.error(f"Ошибка генерации: {e}")
        await msg.answer("❌ Не удалось нарисовать. Попробуй ещё раз.")
