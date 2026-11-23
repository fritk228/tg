from telethon import TelegramClient, events
import os
import asyncio

# ВСТАВЬ СВОИ ДАННЫЕ (api_id и api_hash)
api_id = 8
api_hash = '7245de8e747a0d6fbe11f7cc14fcc0bb'

save_dir = "saved_media"
if not os.path.exists(save_dir):
    os.makedirs(save_dir)

client = TelegramClient('my_secret_session', api_id, api_hash)

# Словарь для временного хранения сообщений (чтобы знать, что удалили)
message_cache = {}

# 1. ЛОВИМ ВСЁ, ЧТО ПРИХОДИТ
@client.on(events.NewMessage(incoming=True))
async def new_message_handler(event):
    # А) Если это самоудаляющееся медиа
    if event.message.media:
        ttl = getattr(event.message.media, 'ttl_seconds', None)
        if ttl:
            print(f"🔥 Поймал самоудаляющееся медиа!")
            file_path = await event.download_media(file=f"{save_dir}/")
            if file_path:
                await client.send_file('me', file_path, caption="👁️ Самоудаляющееся фото/видео")
                os.remove(file_path) # Удаляем с компа, чтобы не забивать
            return # Дальше не проверяем

    # Б) Сохраняем обычные сообщения в кэш (текст или фото)
    if event.message.text:
        message_cache[event.message.id] = event.message.text
    elif event.message.media:
        # Если это обычное фото, скачиваем его, чтобы сохранить на случай удаления
        if event.message.photo:
            file_path = await event.download_media(file=f"{save_dir}/")
            message_cache[event.message.id] = f"[ФОТО] Сохранено в папку: {file_path}"
        else:
            message_cache[event.message.id] = "[Медиа/Видео] (текст не сохранен)"

    # Ограничиваем память (храним последние 500 сообщений, чтобы не завис)
    if len(message_cache) > 500:
        first_key = next(iter(message_cache))
        del message_cache[first_key]


# 2. ЛОВИМ УДАЛЕНИЯ
@client.on(events.MessageDeleted)
async def deleted_message_handler(event):
    for msg_id in event.deleted_ids:
        print(f"🗑️ Сообщение с ID {msg_id} удалено.")
        
        if msg_id in message_cache:
            # Достаем удаленный текст из нашей памяти
            deleted_content = message_cache.pop(msg_id)
            chat_id = getattr(event, 'chat_id', None) or getattr(event, 'sender_id', None)
            
            # Отправляем в "Избранное" (Saved Messages)
            await client.send_message('me', f"🗑️ **УДАЛЕНО В ЧАТЕ** ({chat_id}):\n{deleted_content}")
        else:
            # Если сообщение было отправлено до запуска скрипта, мы его не знаем
            pass

async def main():
    print("🚀 Шпионский скрипт запущен. Слушаю чаты...")
    print("⚠️ ВАЖНО: Не запускай на основном аккаунте, используй симку-заглушку!")
    await client.start()
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())