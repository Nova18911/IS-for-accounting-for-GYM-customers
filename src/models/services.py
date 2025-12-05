from typing import Optional
from datetime import datetime


class Service:
    """Модель услуги/типа тренировки"""

    def __init__(self,
                 id: Optional[int] = None,
                 name: str = "",
                 description: str = "",
                 duration_minutes: int = 60,  # Продолжительность в минутах
                 price: float = 0.0,
                 hall_id: Optional[int] = None,
                 trainer_type_required: str = "any",  # any/group/personal
                 max_participants: int = 1,
                 is_active: bool = True):

        self.id = id
        self.name = name
        self.description = description
        self.duration_minutes = duration_minutes
        self.price = price
        self.hall_id = hall_id
        self.trainer_type_required = trainer_type_required
        self.max_participants = max_participants
        self.is_active = is_active
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    @property
    def duration_formatted(self) -> str:
        """Форматированная продолжительность"""
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60

        if hours > 0:
            return f"{hours} ч {minutes} мин"
        return f"{minutes} мин"

    @property
    def price_formatted(self) -> str:
        """Форматированная цена"""
        return f"{self.price:.2f} руб."

    def to_dict(self) -> dict:
        """Преобразование в словарь для БД"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'duration_minutes': self.duration_minutes,
            'price': self.price,
            'hall_id': self.hall_id,
            'trainer_type_required': self.trainer_type_required,
            'max_participants': self.max_participants,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Service':
        """Создание объекта из словаря БД"""
        return cls(
            id=data.get('id'),
            name=data.get('name', ''),
            description=data.get('description', ''),
            duration_minutes=data.get('duration_minutes', 60),
            price=float(data.get('price', 0)),
            hall_id=data.get('hall_id'),
            trainer_type_required=data.get('trainer_type_required', 'any'),
            max_participants=data.get('max_participants', 1),
            is_active=bool(data.get('is_active', True))
        )

    def validate(self) -> tuple[bool, str]:
        """Валидация данных услуги"""
        errors = []

        if not self.name.strip():
            errors.append("Название услуги обязательно")

        if self.duration_minutes <= 0:
            errors.append("Продолжительность должна быть положительной")

        if self.price < 0:
            errors.append("Цена не может быть отрицательной")

        if self.max_participants <= 0:
            errors.append("Макс. количество участников должно быть положительным")

        if self.trainer_type_required not in ['any', 'group', 'personal']:
            errors.append("Некорректный тип требуемого тренера")

        if errors:
            return False, "; ".join(errors)
        return True, "OK"

    def update_pricing(self, price: float = None, duration_minutes: int = None):
        """Обновить цену и продолжительность"""
        if price is not None:
            self.price = price
        if duration_minutes is not None:
            self.duration_minutes = duration_minutes

        self.updated_at = datetime.now()

    def __str__(self):
        return f"{self.name} - {self.price_formatted} ({self.duration_formatted})"