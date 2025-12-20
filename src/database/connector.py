import pymysql
import time
from typing import Optional, List, Tuple


class DatabaseConnector:

    def __init__(
            self,
            host='5.183.188.132',
            user='2025_mysql__usr8',
            password='91LeBUlsnevGA7cz',
            database='2025_mysql_art',
            charset='utf8mb4'
    ):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.charset = charset

        self.connection = None
        self.cursor = None
        self.max_retries = 3


    def connect(self) -> bool:
        """Подключение к MySQL с 3 попытками."""

        for attempt in range(1, self.max_retries + 1):

            try:
                self.connection = pymysql.connect(
                    host=self.host,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    charset=self.charset,
                    autocommit=True
                )
                self.cursor = self.connection.cursor()
                return True

            except pymysql.MySQLError as e:
                print(f"[Ошибка] Не удалось подключиться (попытка {attempt}): {e}")
                time.sleep(1)

        print("[ФАТАЛЬНО] Подключение к MySQL не удалось после всех попыток.")
        return False


    def reconnect_if_needed(self) -> bool:
        """Проверяет соединение и переподключается при необходимости."""
        try:
            if self.connection is None or self.cursor is None:
                return self.connect()

            self.cursor.execute("SELECT 1")
            return True

        except pymysql.MySQLError:
            print("Соединение потеряно. Переподключение...")
            self.close()
            return self.connect()


    def execute_query(
            self,
            query: str,
            params: Optional[Tuple] = None
    ) -> Optional[List[Tuple]]:


        if not self.reconnect_if_needed():
            return None

        try:
            self.cursor.execute(query, params)

            # SELECT запрос
            if query.strip().upper().startswith("SELECT"):
                return self.cursor.fetchall()

            # Остальные (INSERT, UPDATE, DELETE)
            self.connection.commit()
            return self.cursor.rowcount

        except pymysql.MySQLError as e:
            print(f"Ошибка запроса: {e}")
            return None


    def get_last_insert_id(self) -> Optional[int]:
        """Возвращает ID последней вставленной строки."""
        try:
            self.cursor.execute("SELECT LAST_INSERT_ID()")
            row = self.cursor.fetchone()
            if row:
                return row[0]
        except pymysql.MySQLError as e:
            print(f"[Ошибка] LAST_INSERT_ID(): {e}")

        return None

    def close(self):
        """Закрывает соединение."""
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

    def execute_sql_file(self, file_path: str) -> bool:
        """Считывает SQL-файл и выполняет команды по одной."""
        if not self.reconnect_if_needed():
            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                # Разделяем файл на отдельные запросы по точке с запятой
                sql_commands = f.read().split(';')

            for command in sql_commands:
                if command.strip():  # Пропускаем пустые строки
                    self.cursor.execute(command)

            self.connection.commit()
            return True

        except (FileNotFoundError, pymysql.MySQLError) as e:
            print(f"[Ошибка] Не удалось выполнить SQL-файл {file_path}: {e}")
            return False

db = DatabaseConnector()