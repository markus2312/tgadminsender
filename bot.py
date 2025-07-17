import os
import re
import base64
import asyncio
import tempfile
import gspread

from telethon import TelegramClient, events
from oauth2client.service_account import ServiceAccountCredentials
from config import API_ID, API_HASH, SESSION_NAME

# === Декодирование GOOGLE_CREDENTIALS_BASE64 ===
def decode_credentials_from_env():
    b64_data = os.environ.get("GOOGLE_CREDENTIALS_BASE64")
    if not b64_data:
        raise ValueError("GOOGLE_CREDENTIALS_BASE64 не установлена.")
    json_data = base64.b64decode(b64_data).decode("utf-8")
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    with open(tmp_file.name, 'w') as f:
        f.write(json_data)
    return tmp_file.name

# === Подключение к Google Sheets ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials_path = decode_credentials_from_env()
creds = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)
client_gs = gspread.authorize(creds)

GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "КАДРОФФ TG реакции бот")
sheet = client_gs.open(GOOGLE_SHEET_NAME).sheet1

def load_rules():
    data = sheet.get_all_records()
    rules = []
    for row in data:
        keyword = str(row.get('Кодовое слово', '')).strip().lower()
        reaction = str(row.get('Реакция', '')).strip()
        link = row.get('Ссылка на пост', '')
        message = row.get('Сообщение', '')
        rules.append({'keyword': keyword, 'reaction': reaction, 'link': link, 'message': message})
    return rules

rules = load_rules()

bot = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# Парсим username и msg_id из ссылок
async def get_post_ids():
    post_map = {}
    for rule in rules:
        match = re.search(r't\.me/([\w\d_]+)/(\d+)', rule['link'])
        if match:
            username, msg_id = match.group(1), int(match.group(2))
            rule['username'] = username
            rule['msg_id'] = msg_id
            post_map.setdefault((username, msg_id), []).append(rule)
    return post_map

@bot.on(events.NewMessage)
async def handler_comment(event):
    if not event.is_reply:
        return
    sender = await event.get_sender()
    reply_msg = await event.get_reply_message()
    chat = await event.get_chat()

    if not hasattr(reply_msg, 'id') or not hasattr(chat, 'username'):
        return

    key = (chat.username, reply_msg.id)
    if key not in post_map:
        return

    text = event.message.message.lower()
    for rule in post_map[key]:
        if rule['keyword'] in text:
            try:
                await bot.send_message(sender.id, rule['message'])
            except Exception as e:
                print(f"Ошибка отправки: {e}")

async def main():
    await bot.start()  # стартуем клиента (если сессия валидна, не требует ввода)
    global post_map
    post_map = await get_post_ids()
    print("Бот запущен. Ожидаю события...")
    await bot.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())
