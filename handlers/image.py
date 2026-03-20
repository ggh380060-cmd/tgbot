"""
Генерация картинок через Pollinations.AI — полностью бесплатно.
Команда: /image [описание]
"""

import logging
from aiogram import Router
from aiogram.types import Message, BufferedInputFile
from aiogram.filters import Command
from services.ai_service import generate_image, improve_image_prompt
from services.storage import storage

log = logging.getLogger("image")
router = Router()

EXAMPLES = [
    "кот в космосе, цифровое искусство",
    "закат над Токио, аниме стиль",
    "портрет девушки, масляная живопись",
    "футуристический город ночью",
    "уютная кофейня в дождь",
]


@router.message(Command("image", "img", "рисуй", "нарисуй"))
async def cmd_image(msg: Message):
    user_id = msg.from_user.id

    # Достаём описание из сообщения
    parts = msg.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        ex = "\n".join(f"• <code>/image {e}</code>" for e in EXAMPLES)
        await msg.answer(
            "🖼 <b>Напиши описание после команды:</b>\n\n"
            f"{ex}\n\n"
            "<i>Можно по-русски — переведу сам!</i>"
        )
        return

    prompt = parts[1].strip()

    if not storage.can_image(user_id):
        s = storage.get_stats(user_id)
        await msg.answer(
            f"⚠️ Лимит картинок на сегодня: {s['images']}/{s['images_max']}.\n"
            "Лимит сбросится завтра в полночь 🌙"
        )
        return

    # Сообщение о процессе
    wait = await msg.answer(
        f"🎨 Рисую: «{prompt[:50]}»\n"
        "<i>Обычно 10–25 секунд...</i>"
    )

    try:
        # Улучшаем промпт через Groq (бесплатно)
        improved = await improve_image_prompt(prompt)

        # Генерируем картинку через Pollinations (бесплатно)
        image_bytes = await generate_image(improved)

        storage.inc_image(user_id)
        await wait.delete()

        photo = BufferedInputFile(image_bytes, filename="image.png")
        await msg.answer_photo(
            photo=photo,
            caption=(
                f"🖼 Готово!\n"
                f"📝 Запрос: <i>{prompt}</i>"
            ),
        )

        log.info(f"Картинка: user={user_id}, промпт='{prompt[:30]}'")

    except Exception as e:
        await wait.delete()
        log.error(f"Ошибка генерации user={user_id}: {e}")

        err = str(e).lower()
        if "timeout" in err:
            msg_text = "⏰ Генерация заняла слишком много времени. Попробуй ещё раз — Pollinations иногда медлит."
        elif "403" in err or "400" in err:
            msg_text = "🚫 Такое описание не получилось сгенерировать. Попробуй другое."
        else:
            msg_text = "❌ Не удалось нарисовать. Попробуй через минуту."

        await msg.answer(msg_text)
