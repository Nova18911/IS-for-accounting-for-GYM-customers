# src/models/simple_repositories.py
from src.database.connector import db  # Ваш модуль подключения к БД
from typing import List, Optional
from .halls import Hall
from .services import Service


class HallRepository:
    """Простой репозиторий для работы с залами"""

    @staticmethod
    def get_all(active_only: bool = True) -> List[Hall]:
        """Получить все залы"""
        if active_only:
            query = "SELECT * FROM halls WHERE is_active = TRUE ORDER BY name"
        else:
            query = "SELECT * FROM halls ORDER BY name"

        results = db.execute_query(query)
        return [Hall.from_dict(row) for row in results] if results else []

    @staticmethod
    def get_by_id(hall_id: int) -> Optional[Hall]:
        """Получить зал по ID"""
        query = "SELECT * FROM halls WHERE id = %s"
        result = db.execute_query(query, (hall_id,))
        return Hall.from_dict(result[0]) if result else None

    @staticmethod
    def create(hall: Hall) -> Optional[Hall]:
        """Создать новый зал"""
        query = """
        INSERT INTO halls (name, capacity, color, description, equipment, is_active)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (hall.name, hall.capacity, hall.color,
                  hall.description, hall.equipment, hall.is_active)

        result = db.execute_query(query, values)
        if result:
            hall.id = result  # Получаем ID новой записи
            return hall
        return None

    @staticmethod
    def update(hall: Hall) -> bool:
        """Обновить зал"""
        query = """
        UPDATE halls 
        SET name = %s, capacity = %s, color = %s, 
            description = %s, equipment = %s, is_active = %s
        WHERE id = %s
        """
        values = (hall.name, hall.capacity, hall.color,
                  hall.description, hall.equipment, hall.is_active, hall.id)

        return db.execute_query(query, values) is not None

    @staticmethod
    def delete(hall_id: int) -> bool:
        """Деактивировать зал"""
        query = "UPDATE halls SET is_active = FALSE WHERE id = %s"
        return db.execute_query(query, (hall_id,)) is not None


class ServiceRepository:
    """Простой репозиторий для работы с услугами"""

    @staticmethod
    def get_all(active_only: bool = True) -> List[Service]:
        """Получить все услуги"""
        if active_only:
            query = "SELECT * FROM services WHERE is_active = TRUE ORDER BY name"
        else:
            query = "SELECT * FROM services ORDER BY name"

        results = db.execute_query(query)
        return [Service.from_dict(row) for row in results] if results else []

    @staticmethod
    def get_by_id(service_id: int) -> Optional[Service]:
        """Получить услугу по ID"""
        query = "SELECT * FROM services WHERE id = %s"
        result = db.execute_query(query, (service_id,))
        return Service.from_dict(result[0]) if result else None

    @staticmethod
    def get_by_hall(hall_id: int) -> List[Service]:
        """Получить услуги для конкретного зала"""
        query = "SELECT * FROM services WHERE hall_id = %s AND is_active = TRUE"
        results = db.execute_query(query, (hall_id,))
        return [Service.from_dict(row) for row in results] if results else []

    @staticmethod
    def create(service: Service) -> Optional[Service]:
        """Создать новую услугу"""
        query = """
        INSERT INTO services 
        (name, description, duration_minutes, price, hall_id, 
         trainer_type_required, max_participants, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (service.name, service.description, service.duration_minutes,
                  service.price, service.hall_id, service.trainer_type_required,
                  service.max_participants, service.is_active)

        result = db.execute_query(query, values)
        if result:
            service.id = result
            return service
        return None

    @staticmethod
    def update(service: Service) -> bool:
        """Обновить услугу"""
        query = """
        UPDATE services 
        SET name = %s, description = %s, duration_minutes = %s, price = %s,
            hall_id = %s, trainer_type_required = %s, max_participants = %s, is_active = %s
        WHERE id = %s
        """
        values = (service.name, service.description, service.duration_minutes,
                  service.price, service.hall_id, service.trainer_type_required,
                  service.max_participants, service.is_active, service.id)

        return db.execute_query(query, values) is not None

    @staticmethod
    def delete(service_id: int) -> bool:
        """Деактивировать услугу"""
        query = "UPDATE services SET is_active = FALSE WHERE id = %s"
        return db.execute_query(query, (service_id,)) is not None