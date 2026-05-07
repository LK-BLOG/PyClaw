from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    """所有Tool的基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def intent_type(self):
        """对应的IntentType"""
        pass

    @abstractmethod
    def execute(self, **params) -> Any:
        pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "intent_type": self.intent_type.value
        }
