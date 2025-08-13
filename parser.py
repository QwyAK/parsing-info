import asyncio
from telethon import TelegramClient
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch, PeerUser
from telethon.tl.functions.users import GetFullUserRequest
import pymysql
from datetime import datetime
import config

def connect_db():
    return pymysql.connect(
        host=config.MYSQL_CONFIG['host'],
        user=config.MYSQL_CONFIG['user'],
        password=config.MYSQL_CONFIG['password'],
        database=config.MYSQL_CONFIG['database'],
        charset=config.MYSQL_CONFIG['charset']
    )

def save_user(user_data):
    connection = connect_db()
    try:
        with connection.cursor() as cursor:
            sql = """
            INSERT INTO users (id, username, phone, first_name, last_name, bio, is_bot, status, last_seen)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                username = VALUES(username),
                phone = VALUES(phone),
                first_name = VALUES(first_name),
                last_name = VALUES(last_name),
                bio = VALUES(bio),
                status = VALUES(status),
                last_seen = VALUES(last_seen)
            """
            cursor.execute(sql, (
                user_data['id'],
                user_data['username'],
                user_data['phone'],
                user_data['first_name'],
                user_data['last_name'],
                user_data['bio'],
                user_data['is_bot'],
                user_data['status'],
                user_data['last_seen']
            ))
        connection.commit()
    finally:
        connection.close()

def get_status_string(status):
    if hasattr(status, 'was_online'):
        return 'online', status.was_online
    elif hasattr(status, 'expires'):
        return 'away', None
    else:
        return str(status).split('.')[-1], None

async def main():
    client = TelegramClient('session_user', config.API_ID, config.API_HASH)

    await client.start()
    print("Клиент запущен и авторизован.")

    try:
        entity = await client.get_entity(config.GROUP_ID)
        
        if not hasattr(entity, 'participants_count'):
            print("Ошибка: это не публичная группа или канал.")
            return

        print(f"Парсим участников группы: {entity.title} (участников: {entity.participants_count})")

        offset = 0
        limit = 200
        collected = 0

        while True:
            participants = await client(GetParticipantsRequest(
                channel=entity,
                filter=ChannelParticipantsSearch(''),
                offset=offset,
                limit=limit,
                hash=0
            ))

            if not participants.users:
                break

            for user in participants.users:
                try:
                    full_user = await client(GetFullUserRequest(user))

                    user_info = {
                        'id': user.id,
                        'username': user.username,
                        'phone': user.phone if hasattr(user, 'phone') else None,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'is_bot': user.bot,
                        'bio': full_user.full_user.about or None,
                    }

                    status_info, last_seen = get_status_string(user.status)
                    user_info['status'] = status_info
                    user_info['last_seen'] = last_seen.strftime('%Y-%m-%d %H:%M:%S') if last_seen else None

                    save_user(user_info)
                    collected += 1
                    print(f"Сохранён: {user.username or user.first_name} | ID: {user.id}")

                except Exception as e:
                    print(f"Ошибка при обработке пользователя {user.id}: {e}")
                    continue

            offset += len(participants.users)
            if len(participants.users) < limit:
                break

            print(f"Обработано {offset} участников...")

        print(f"✅ Парсинг завершён. Сохранено {collected} пользователей.")

    except Exception as e:
        print(f"Ошибка при получении группы: {e}")

    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())