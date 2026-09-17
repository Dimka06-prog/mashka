"""Управление пользователями и их состояниями."""
from typing import Dict, Optional


class UserManager:
    """Менеджер пользователей для хранения состояний."""
    
    def __init__(self):
        """Инициализация менеджера пользователей."""
        self.users: Dict[int, Dict] = {}
    
    def get_user_state(self, user_id: int) -> Dict:
        """Получить состояние пользователя."""
        return self.users.setdefault(user_id, {})
    
    def set_user_state(self, user_id: int, state: Dict) -> None:
        """Установить состояние пользователя."""
        self.users[user_id] = state
    
    def reset_user(self, user_id: int) -> None:
        """Сбросить состояние пользователя."""
        self.users[user_id] = {}
    
    def get_user_field(self, user_id: int, field: str, default=None):
        """Получить конкретное поле состояния пользователя."""
        state = self.get_user_state(user_id)
        return state.get(field, default)
    
    def set_user_field(self, user_id: int, field: str, value) -> None:
        """Установить конкретное поле состояния пользователя."""
        state = self.get_user_state(user_id)
        state[field] = value
    
    def clear_all(self) -> None:
        """Очистить всех пользователей (для тестирования)."""
        self.users.clear()


# Глобальный экземпляр менеджера пользователей
user_manager = UserManager()
