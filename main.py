import os
import textwrap
from telebot import TeleBot
import telegramify_markdown
import telegramify_markdown.customize as customize
from telebot.types import Message, Document
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("TOKEN")

# Настройки библиотеки
customize.strict_markdown = False

MAX_MESSAGE_LENGTH = 4096  # Максимальный размер сообщения в Telegram

bot = TeleBot(TOKEN)

def split_message(text, max_length):
    """Разбивает сообщение на части, избегая разрыва внутри форматирования Markdown, включая код."""
    parts = []
    current_part = ""
    in_code_block = False
    code_block_start = "```"
    i = 0

    while i < len(text):
        # Проверяем начало или конец блока кода
        if text[i:i+3] == code_block_start:
            in_code_block = not in_code_block
            current_part += code_block_start
            i += 3
            continue

        # Добавляем символ в текущую часть
        current_part += text[i]
        i += 1

        # Если длина текущей части достигла предела и мы не в кодовом блоке
        if len(current_part) >= max_length and not in_code_block:
            # Ищем подходящее место для разрыва (например, перенос строки)
            split_index = current_part.rfind('\n')
            if split_index == -1:
                split_index = max_length
            parts.append(current_part[:split_index])
            current_part = current_part[split_index:].lstrip()

    # Добавляем оставшуюся часть
    if current_part:
        parts.append(current_part)

    # Проверяем, что все кодовые блоки закрыты
    if in_code_block:
        parts[-1] += "\n```"  # Закрываем незавершенный блок кода

    return parts

@bot.message_handler(content_types=['document'])
def handle_document(message: Message):
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    raw_text = downloaded_file.decode("utf-8")
    can_be_sent = telegramify_markdown.markdownify(textwrap.dedent(raw_text))
    
    # Разделяем сообщение безопасно
    for part in split_message(can_be_sent, MAX_MESSAGE_LENGTH):
        bot.send_message(message.chat.id, part, parse_mode="MarkdownV2")

@bot.message_handler(func=lambda message: True)
def default_response(message: Message):
    bot.send_message(message.chat.id, "Пожалуйста, отправьте Markdown-файл для обработки.")

print("Бот запущен...")
bot.polling()
