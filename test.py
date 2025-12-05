from src.database.connector import db


def simple_init():
    # Подключаемся и создаем структуру
    if db.connect(host='5.183.188.132', user='2025_mysql__usr8',
                  password='91LeBUlsnevGA7cz', database='2025_mysql_art'):
        print("Инициализация базы данных...")

        # Выполняем schema.sql
        success = db.execute_sql_file('database/schema.sql')

        if success:
            print("База данных успешно инициализирована!")
        else:
            print("Ошибка инициализации базы данных")

        db.close()


if __name__ == "__main__":
    simple_init()