# -*- coding: utf-8 -*-
"""
Плагин для exteraGram: Улучшение текста сообщений
"""

import re
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

# --- Метаданные плагина ---
__plugin_name__ = "Text Enhancer"
__version__ = "1.0.0"
__author__ = "@your_username"
__description__ = "Улучшает текст сообщения по нажатию команды или кнопки."


# --- Функция логики улучшения текста ---
def enhance_text_logic(text: str) -> str:
    """
    Базовая логика улучшения текста:
    - Исправление двойных пробелов
    - Капитализация первых букв предложений
    - Форматирование знаков препинания (пробел ПОСЛЕ знака, но не ДО)
    - Базовые типографические правила (тире вместо дефиса-тире и т.д.)
    """
    if not text:
        return text

    # 1. Удаление множественных пробелов
    text = re.sub(r'[ \t]+', ' ', text)

    # 2. Исправление пробелов вокруг знаков препинания (. , ! ? :)
    text = re.sub(r'\s+([.,!?:])', r'\1', text)
    text = re.sub(r'([.,!?:])(?=[^\s.,!?:0-9])', r'\1 ', text)

    # 3. Замена простых дефисов-тире на длинное тире
    text = re.sub(r'(\s)-(\s)', r'\1—\2', text)

    # 4. Делаем первую букву предложений заглавной
    sentences = re.split(r'(?<=[.!?])\s+', text)
    formatted_sentences = [s.capitalize() if s else s for s in sentences]
    
    return " ".join(formatted_sentences).strip()


# --- 1. Способ через команду .enhance в ответ на сообщение ---
@Client.on_message(filters.me & filters.command(["enhance", "улучшить"], prefixes="."))
async def enhance_message_command(client: Client, message: Message):
    """
    Вызывается командой .enhance или .улучшить в ответ на ваше сообщение 
    или напрямую с текстом (например: `.улучшить привет  как дела`).
    """
    # Если команда отправлена в ответ на сообщение
    target_msg = message.reply_to_message if message.reply_to_message else message
    
    # Получаем исходный текст
    original_text = ""
    if message.reply_to_message:
        original_text = target_msg.text or target_msg.caption or ""
    else:
        # Если текст идет сразу за командой
        original_text = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else ""

    if not original_text:
        await message.edit_text("❌ **Ошибка:** Не найден текст для улучшения.")
        return

    # Улучшаем текст
    new_text = enhance_text_logic(original_text)

    if message.reply_to_message:
        # Редактируем целевое сообщение и удаляем саму команду
        await target_msg.edit_text(new_text)
        await message.delete()
    else:
        # Редактируем текущее сообщение
        await message.edit_text(new_text)


# --- 2. Способ через создание сообщения с кнопкой «Улучшить» ---
@Client.on_message(filters.me & filters.command("draft", prefixes="."))
async def create_draft_with_button(client: Client, message: Message):
    """
    Команда `.draft Ваш текст`
    Отправляет текст с прикрепленной inline-кнопкой «✨ Улучшить».
    """
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.edit_text("ℹ️ **Использование:** `.draft Ваш неоптимизированный  текст`")
        return

    text = args[1]
    
    # Клавиатура с кнопкой
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ Улучшить текст", callback_data="enhance_this_msg")]
    ])

    await message.edit_text(text, reply_markup=keyboard)


# --- 3. Обработчик нажатия на кнопку ---
@Client.on_callback_query(filters.regex("^enhance_this_msg$"))
async def on_enhance_button_click(client: Client, callback_query: CallbackQuery):
    """
    Обрабатывает клик по кнопке «Улучшить текст».
    """
    current_text = callback_query.message.text or callback_query.message.caption or ""
    
    if not current_text:
        await callback_query.answer("Текст не найден!", show_alert=True)
        return

    # Применяем улучшения
    enhanced = enhance_text_logic(current_text)

    if enhanced == current_text:
        await callback_query.answer("Текст уже идеально оформлен!", show_alert=False)
        return

    # Обновляем сообщение (убираем кнопку после улучшения)
    await callback_query.message.edit_text(enhanced, reply_markup=None)
    await callback_query.answer("✨ Текст успешно улучшен!")
