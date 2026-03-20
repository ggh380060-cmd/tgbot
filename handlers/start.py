"""
Стартовые команды: /start, /help, /new, /stats
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.storage import storage

log = logging.getLogger("start")
router = Router()

WELCOME = """👋 <b>Привет! Я ИИ-бот на базе Llama 3.3</b>

Что умею:
💬 <b>Чат</b> — отвечу на любой вопрос
🖼 <b>Картинки</b> — /image [описание]
📸 <b>Анализ фото</b> — пришли фото, опишу что на нём
🆕 <b>Сброс диалога</b> — /new
📊 <b>Статистика</b> — /stats

<i>Просто напиши что-нибудь — начнём!</i>
"""

HELP = """📖 <b>Команды бота:</b>

<b>Чат:</b>
• Пиши любое сообщение — отвечу
• /new — начать разговор заново

<b>Картинки:</b>
• /image [описание] — нарисую
  Пример: <code>/image кот в космосе</code>
• Пришли фото — опишу что на нём

<b>Прочее:</b>
• /stats — сколько запросов осталось
• /help — это меню

<b>Лимиты (сбрасываются в полночь):</b>
• Чат: 100 сообщений/день
• Картинки: 20 штук/день
"""


def kb_main():
    b = InlineKeyboardBuilder()
    b.button(text="💬 Начать чат", callback_data="hint_chat")
    b.button(text="🖼 Нарисовать", callback_data="hint_image")
    b.button(text="📊 Статистика", callback_data="show_stats")
    b.button(text="📖 Помощь", callback_data="show_help")
    b.adjust(2, 2)
    return b.as_markup()


@router.message(CommandStart())
async def cmd_start(msg: Message):
    log.info(f"/start от user_id={msg.from_user.id} name={msg.from_user.first_name}")
    await msg.answer(WELCOME, reply_markup=kb_main())


@router.message(Command("help"))
async def cmd_help(msg: Message):
    await msg.answer(HELP)


@router.message(Command("new"))
async def cmd_new(msg: Message):
    n = storage.clear_history(msg.from_user.id)
    await msg.answer(f"🆕 Диалог очищен! Удалено {n} сообщений.\nНачнём с чистого листа.")


@router.message(Command("stats"))
async def cmd_stats(msg: Message):
    s = storage.get_stats(msg.from_user.id)
    await msg.answer(
        f"📊 <b>Статистика за сегодня:</b>\n\n"
        f"💬 Чат: {s['chats']} / {s['chats_max']}\n"
        f"🖼 Картинки: {s['images']} / {s['images_max']}\n"
        f"🧠 Сообщений в памяти: {s['history']}\n\n"
        f"<i>Лимиты сбрасываются каждый день в 00:00</i>"
    )


# ── Колбэки кнопок ────────────────────────────────────────────

@router.callback_query(F.data == "show_help")
async def cb_help(cb: CallbackQuery):
    await cb.message.edit_text(HELP)
    await cb.answer()

@router.callback_query(F.data == "show_stats")
async def cb_stats(cb: CallbackQuery):
    s = storage.get_stats(cb.from_user.id)
    await cb.message.edit_text(
        f"📊 <b>Статистика за сегодня:</b>\n\n"
        f"💬 Чат: {s['chats']} / {s['chats_max']}\n"
        f"🖼 Картинки: {s['images']} / {s['images_max']}\n"
        f"🧠 Сообщений в памяти: {s['history']}"
    )
    await cb.answer()

@router.callback_query(F.data == "hint_chat")
async def cb_hint_chat(cb: CallbackQuery):
    await cb.message.edit_text(
        "💬 <b>Как пользоваться чатом:</b>\n\n"
        "Просто напиши любое сообщение!\n\n"
        "Я помню наш разговор (последние 20 сообщений).\n"
        "Чтобы начать заново — /new"
    )
    await cb.answer()

@router.callback_query(F.data == "hint_image")
async def cb_hint_image(cb: CallbackQuery):
    await cb.message.edit_text(
        "🖼 <b>Как сгенерировать картинку:</b>\n\n"
        "Команда: /image [описание]\n\n"
        "<b>Примеры:</b>\n"
        "• <code>/image котик в космосе</code>\n"
        "• <code>/image закат над горами, масляная живопись</code>\n"
        "• <code>/image футуристический город ночью</code>\n\n"
        "Можно писать по-русски — сам переведу!"
    )
    await cb.answer()
