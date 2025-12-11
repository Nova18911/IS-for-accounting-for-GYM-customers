# src/database/connector.py
import pymysql
import time
from typing import Optional, List, Tuple


class DatabaseConnector:
    """Класс для работы с базой данных MySQL"""

    def __init__(self, host='5.183.188.132', user='2025_mysql__usr8',
                 password='91LeBUlsnevGA7cz',
                 database='2025_mysql_art', charset='utf8mb4'):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.charset = charset
        self.connection = None
        self.cursor = None
        self.max_retries = 3  # Максимальное количество попыток переподключения

    def connect(self) -> bool:
        """Подключение к базе данных с повторными попытками"""
        for attempt in range(self.max_retries):
            try:
                self.connection = pymysql.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    charset=self.charset,
                    connect_timeout=30,  # Таймаут подключения 30 секунд
                    read_timeout=30,  # Таймаут чтения 30 секунд
                    write_timeout=30,  # Таймаут записи 30 секунд
                    autocommit=True  # Автокоммит для каждой операции
                )

                self.cursor = self.connection.cursor()
                print(f"Успешное подключение к базе данных (попытка {attempt + 1})")
                return True

            except pymysql.Error as e:
                print(f"Ошибка подключения (попытка {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2)  # Ждем 2 секунды перед следующей попыткой
                else:
                    return False
        return False

    def execute_sql_file(self, filepath: str) -> bool:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                sql_commands = f.read()

            for command in sql_commands.split(';'):
                cmd = command.strip()
                if cmd:
                    self.cursor.execute(cmd)

            self.connection.commit()
            return True

        except Exception as e:
            print("Ошибка execute_sql_file:", e)
            return False

    def reconnect_if_needed(self) -> bool:
        """Проверить и переподключиться при необходимости"""
        try:
            # Простой способ проверить соединение
            self.cursor.execute("SELECT 1")
            return True
        except (pymysql.Error, AttributeError):
            print("Соединение разорвано, пытаюсь переподключиться...")
            self.close()
            return self.connect()

    def execute_query(self, query: str, params: Optional[Tuple] = None) -> Optional[List[Tuple]]:
        """Выполнить SQL запрос с обработкой ошибок и переподключением"""
        if not self.reconnect_if_needed():
            print("Не удалось переподключиться к базе данных")
            return None

        try:
            self.cursor.execute(query, params)

            # Если это SELECT запрос, возвращаем результат
            if query.strip().upper().startswith('SELECT'):
                return self.cursor.fetchall()
            else:
                # Для INSERT, UPDATE, DELETE коммитим изменения
                self.connection.commit()
                return self.cursor.rowcount  # Возвращаем количество затронутых строк

        except pymysql.Error as e:
            print(f"Ошибка выполнения запроса: {e}")
            try:
                self.connection.rollback()  # Откатываем изменения при ошибке
            except:
                pass
            return None

    def get_last_insert_id(self) -> Optional[int]:
        """Получить ID последней вставленной записи"""
        if not self.reconnect_if_needed():
            return None

        try:
            self.cursor.execute("SELECT LAST_INSERT_ID()")
            result = self.cursor.fetchone()
            return result[0] if result else None
        except pymysql.Error as e:
            print(f"Ошибка получения последнего ID: {e}")
            return None

    def close(self):
        """Закрыть соединение с базой данных"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
        except:
            pass
        finally:
            self.cursor = None
            self.connection = None


# Создаем глобальный экземпляр connector
db = DatabaseConnector()