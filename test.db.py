import pymysql
from config import MYSQL_CONFIG  
def test_connection():
    try:
        connection = pymysql.connect(
            host=MYSQL_CONFIG['host'],
            user=MYSQL_CONFIG['user'],
            password=MYSQL_CONFIG['password'],
            database=MYSQL_CONFIG['database'],
            charset='utf8mb4'
        )
        print("✅ Подключение к MySQL успешно!")
        
        with connection.cursor() as cursor:
            cursor.execute("SELECT DATABASE();")
            result = cursor.fetchone()
            print(f"Подключены к базе: {result[0]}")

            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            print("Таблицы:", tables)

        connection.close()
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")

if __name__ == '__main__':
    test_connection()

    юзайте данный файл для отладки при подключении к БД / python test.db.py