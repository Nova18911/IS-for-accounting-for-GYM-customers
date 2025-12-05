# src/models/test_model.py
import sys
import os

# Добавляем путь к проекту для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.connector import db
from src.models.halls import Hall
from src.models.services import Service
from src.models.simple_repository import HallRepository, ServiceRepository


def init_database_connection():
    """Инициализирует подключение к БД"""
    print("Подключаемся к базе данных...")

    # Подключаемся к БД
    if not db.connect():
        print("❌ Не удалось подключиться к БД")
        print("Проверьте параметры подключения в connector.py")
        return False

    print("✅ Подключение успешно")
    return True


def test_halls():
    print("=== Тестирование модели Залы ===")

    # Создаем зал
    hall = Hall(
        name="Основной зал",
        capacity=20,
        color="#3498db",
        description="Основной тренажерный зал",
        equipment="Тренажеры, гантели, штанги"
    )

    # Валидируем
    is_valid, message = hall.validate()
    print(f"Валидация зала: {is_valid}, {message}")
    print(f"Зал: {hall}")

    print()


def test_services():
    print("=== Тестирование модели Услуги ===")

    # Создаем услугу
    service = Service(
        name="Персональная тренировка",
        description="Индивидуальная тренировка с тренером",
        duration_minutes=60,
        price=1500.00,
        hall_id=1,
        trainer_type_required="personal",
        max_participants=1
    )

    # Валидируем
    is_valid, message = service.validate()
    print(f"Валидация услуги: {is_valid}, {message}")
    print(f"Услуга: {service}")
    print(f"Продолжительность: {service.duration_formatted}")
    print(f"Цена: {service.price_formatted}")

    print()


def test_repositories():
    print("=== Тестирование репозиториев ===")

    # Проверяем что таблицы существуют
    print("Проверяем существование таблиц...")

    # Сначала создадим тестовые данные напрямую
    create_test_data()

    # Теперь тестируем репозитории
    print("\nПолучаем данные через репозитории:")

    # Получаем все залы
    halls = HallRepository.get_all()
    print(f"Найдено залов: {len(halls)}")
    for hall in halls:
        print(f"  - {hall.name} ({hall.capacity} чел.)")

    # Получаем все услуги
    services = ServiceRepository.get_all()
    print(f"\nНайдено услуг: {len(services)}")
    for service in services:
        print(f"  - {service.name} - {service.price_formatted}")

    # Получаем услуги для зала
    if halls:
        hall_id = halls[0].id
        hall_services = ServiceRepository.get_by_hall(hall_id)
        print(f"\nУслуги для зала '{halls[0].name}': {len(hall_services)}")
        for service in hall_services:
            print(f"  - {service.name}")


def create_test_data():
    """Создает тестовые данные напрямую через db.execute_query"""
    try:
        # Проверяем есть ли таблицы
        print("Создаем таблицы если их нет...")

        # Таблица залов
        create_halls = """
        CREATE TABLE IF NOT EXISTS halls (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(100) NOT NULL,
            capacity INT NOT NULL DEFAULT 10,
            color VARCHAR(7) DEFAULT '#FFFFFF',
            description TEXT,
            equipment TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
        db.execute_query(create_halls)

        # Таблица услуг
        create_services = """
        CREATE TABLE IF NOT EXISTS services (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            duration_minutes INT NOT NULL DEFAULT 60,
            price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
            hall_id INT,
            trainer_type_required ENUM('any', 'group', 'personal') DEFAULT 'any',
            max_participants INT NOT NULL DEFAULT 1,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """
        db.execute_query(create_services)

        # Проверяем есть ли данные
        check_halls = "SELECT COUNT(*) as count FROM halls"
        result = db.execute_query(check_halls)

        if result and result[0][0] == 0:  # Если таблица пустая
            print("Добавляем тестовые данные...")

            # Добавляем залы
            insert_halls = """
            INSERT INTO halls (name, capacity, color, description) VALUES
            ('Основной зал', 20, '#3498db', 'Основной тренажерный зал с кардио-зоной'),
            ('Групповой зал', 15, '#e74c3c', 'Зал для групповых занятий'),
            ('Бассейн', 10, '#1abc9c', '25-метровый бассейн')
            """
            db.execute_query(insert_halls)

            # Добавляем услуги
            insert_services = """
            INSERT INTO services (name, description, duration_minutes, price, hall_id, trainer_type_required, max_participants) VALUES
            ('Персональная тренировка', 'Индивидуальная тренировка с тренером', 60, 1500.00, 1, 'personal', 1),
            ('Групповая йога', 'Занятия йогой в группе', 90, 500.00, 2, 'group', 15),
            ('Плавание', 'Свободное плавание', 60, 300.00, 3, 'any', 10)
            """
            db.execute_query(insert_services)

            print("✅ Тестовые данные добавлены")
        else:
            print(f"✅ В таблицах уже есть {result[0][0]} записей")

    except Exception as e:
        print(f"Ошибка при создании тестовых данных: {e}")


def main():
    """Основная функция тестирования"""

    # Сначала инициализируем подключение
    if not init_database_connection():
        return

    try:
        # Тестируем модели
        test_halls()
        test_services()

        # Тестируем репозитории
        test_repositories()

        print("\n" + "=" * 50)
        print("✅ Все тесты завершены успешно!")

    finally:
        # Закрываем соединение
        db.close()
        print("Соединение с БД закрыто")


if __name__ == "__main__":
    main()