# execute_user_sql.py
from src.database.connector import db


def execute_user_sql():
    """Выполняет SQL файл с таблицей пользователей"""

    sql_content = """
    CREATE TABLE IF NOT EXISTS users (
        user_id INT PRIMARY KEY AUTO_INCREMENT,
        email VARCHAR(100) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        role ENUM('admin', 'reception', 'trainer') DEFAULT 'reception',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT TRUE
    );

    INSERT INTO users (email, password_hash, role) VALUES
    -- Администратор (пароль: admin123)
    ('admin@fitness.ru', SHA2('admin123', 256), 'admin'),
    -- Ресепшн (пароль: reception123)
    ('reception@fitness.ru', SHA2('reception123', 256), 'reception');
    """

    if db.connect():
        try:
            print("Создание таблицы пользователей...")

            # Разделяем SQL на отдельные запросы
            queries = [q.strip() for q in sql_content.split(';') if q.strip()]

            for query in queries:
                if query:  # Пропускаем пустые
                    print(f"Выполняю: {query[:50]}...")
                    db.execute_query(query)

            print("✅ Таблица users создана!")

            # Проверяем
            result = db.execute_query("SELECT email, role FROM users")
            print("\nСозданные пользователи:")
            for user in result:
                print(f"  - {user[0]} ({user[1]})")

        except Exception as e:
            print(f"❌ Ошибка: {e}")
        finally:
            db.close()
    else:
        print("❌ Не удалось подключиться к БД")


if __name__ == "__main__":
    execute_user_sql()