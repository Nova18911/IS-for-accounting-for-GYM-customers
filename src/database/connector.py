import pymysql
import os

class DatabaseConnector:
    def __init__(self):
        self.connection = None

    def connect(self, host='localhost', user='your_username',
                password='your_password', database='fitness_club'):
        """Подключение к базе данных"""
        try:
            self.connection = pymysql.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                charset='utf8mb4'
                #cursorclass=pymysql.cursors.DictCursor
            )
            print("Успешное подключение к базе данных")
            return True
        except pymysql.Error as e:
            print(f"Ошибка подключения: {e}")
            return False

    def execute_sql_file(self, file_path):
        """Выполнение SQL-файла"""
        if not self.connection:
            print("Нет подключения к БД")
            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                sql_script = file.read()

            # Разделяем скрипт на отдельные запросы
            queries = [q.strip() for q in sql_script.split(';') if q.strip()]

            with self.connection.cursor() as cursor:
                for query in queries:
                    if query:  # Проверяем, что запрос не пустой
                        cursor.execute(query)

            self.connection.commit()
            print(f"SQL-файл {file_path} успешно выполнен")
            return True

        except Exception as e:
            print(f"Ошибка выполнения SQL-файла: {e}")
            self.connection.rollback()
            return False

    def execute_query(self, query, params=None):
        """Выполнение одного SQL-запроса"""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                if query.strip().upper().startswith('SELECT'):
                    return cursor.fetchall()
                else:
                    self.connection.commit()
                    return cursor.rowcount
        except Exception as e:
            print(f"Ошибка выполнения запроса: {e}")
            return None

    def close(self):
        """Закрытие соединения"""
        if self.connection:
            self.connection.close()
            print("Соединение с БД закрыто")


# Создаем глобальный экземпляр connector
db = DatabaseConnector()