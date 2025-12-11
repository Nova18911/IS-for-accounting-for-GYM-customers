from src.database.connector import DatabaseConnector


def simple_init():
    # создаем новый экземпляр с нужными параметрами
    db = DatabaseConnector(
        host='5.183.188.132',
        user='2025_mysql__usr8',
        password='91LeBUlsnevGA7cz',
        database='2025_mysql_art',
    )

    if db.connect():
        print("Инициализация базы данных...")

        success = db.execute_sql_file('database/schema.sql')

        if success:
            print("База данных успешно инициализирована!")
        else:
            print("Ошибка инициализации базы данных")

        db.close()


if __name__ == "__main__":
    simple_init()
