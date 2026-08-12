# -*- coding: utf-8 -*-
"""
Плагин для exteraGram: Text Enhancer
Автоматически форматирует и улучшает пунктуацию/пробелы в сообщениях.
"""

import re
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# --- Метаданные плагина ---
__plugin_name__ = "Text Enhancer"
__version__ = "1.0.0"
__author__ = "@your_username"
__description__ = "Автоматическое форматирование и улучшение текста по кнопке или команде."


def enhance_text_logic(text: str) -> str:
    """Логика очистки и исправления текста."""
    if not text:
        return text

    # Удаляем лишние пробелы и табуляции
    text = re.sub(r'[ \t]+', ' ', text)

    # Исправляем пробелы перед и после знаков препинания
    text = re.sub(r'\s+([.,!?:])', r'\1', text)
    text = re.sub(r'([.,!?:])(?=[^\s.,!?:0-9])', r'\1 ', text)

    # Дефисы с пробелами меняем на тире
    text = re.sub(r'(\s)-(\s)', r'\1—\2', text)

    # Делаем первые буквы предложений заглавными
    sentences = re.split(r'(?<=[.!?])\s+', text)
    formatted = [s.capitalize() if s else s for s in sentences]
    
    return " ".join(formatted).strip()


@Client.on_message(filters.me & filters.command(["enhance", "улучшить"], prefixes="."))
async def enhance_message_command(client: Client, message: Message):
    """Команда .улучшить в ответ на сообщение или сразу с текстом"""
    target_msg = message.reply_to_message if message.reply_to_message else message
    
    if message.reply_to_message:
        original_text = target_msg.text or target_msg.caption or ""
    else:
        args = message.text.split(maxsplit=1)
        original_text = args[1] if len(args) > 1 else ""

    if not original_text:
        await message.edit_text("❌ **Ошибка:** Текст не найден.")
        return

    new_text = enhance_text_logic(original_text)

    if message.reply_to_message:
        await target_msg.edit_text(new_text)
        await message.delete()
    else:
        await message.edit_text(new_text)


@Client.on_message(filters.me & filters.command("draft", prefixes="."))
async def create_draft_with_button(client: Client, message: Message):
    """Команда .draft <текст> создает сообщение с кнопкой улучшения"""
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.edit_text("ℹ️ **Использование:** `.draft ваш текст с  ошибками`")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ Улучшить текст", callback_data="enhance_this_msg")]
    ])
    await message.edit_text(args[1], reply_markup=keyboard)


@Client.on_callback_query(filters.regex("^enhance_this_msg$"))
async def on_enhance_button_click(client: Client, callback_query: CallbackQuery):
    """Обработка клика по кнопке «Улучшить текст»"""
    current_text = callback_query.message.text or callback_query.message.caption or ""
    enhanced = enhance_text_logic(current_text)

    if enhanced == current_text:
        await callback_query.answer("Текст уже оформлен идеально!", show_alert=False)
        return

    await callback_query.message.edit_text(enhanced, reply_markup=None)
    await callback_query.answer("✨ Текст обновлен!")
