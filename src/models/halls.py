from typing import Optional
from datetime import datetime


class Hall:
    """Модель зала фитнес-клуба"""

    def __init__(self,
                 id: Optional[int] = None,
                 name: str = "",
                 capacity: int = 0,
                 color: str = "#FFFFFF",  # Цвет для отображения в расписании
                 description: str = "",
                 equipment: str = "",
                 is_active: bool = True):

        self.id = id
        self.name = name
        self.capacity = capacity
        self.color = color
        self.description = description
        self.equipment = equipment
        self.is_active = is_active
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """Преобразование в словарь для БД"""
        return {
            'id': self.id,
            'name': self.name,
            'capacity': self.capacity,
            'color': self.color,
            'description': self.description,
            'equipment': self.equipment,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Hall':
        """Создание объекта из словаря БД"""
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            capacity=data.get('capacity', 0),
            color=data.get('color', '#FFFFFF'),
            description=data.get('description', ''),
            equipment=data.get('equipment', ''),
            is_active=bool(data.get('is_active', True))
        )

    def validate(self) -> tuple[bool, str]:
        """Валидация данных зала"""
        errors = []

        if not self.name.strip():
            errors.append("Название зала обязательно")

        if self.capacity <= 0:
            errors.append("Вместимость должна быть положительным числом")

        if not self.color.startswith('#'):
            errors.append("Цвет должен быть в формате #FFFFFF")

        if errors:
            return False, "; ".join(errors)
        return True, "OK"

    def update_info(self, name: str = None, capacity: int = None,
                    color: str = None, description: str = None):
        """Обновить информацию о зале"""
        if name is not None:
            self.name = name
        if capacity is not None:
            self.capacity = capacity
        if color is not None:
            self.color = color
        if description is not None:
            self.description = description

        self.updated_at = datetime.now()

    def __str__(self):
        return f"{self.name} (вместимость: {self.capacity})"