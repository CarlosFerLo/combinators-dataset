from pydantic import BaseModel
from abc import ABC, abstractmethod
from typing import Dict
class Type (BaseModel, ABC) :
    """
    Base class for types. All types should inherit from this class.
    """
    
    @abstractmethod
    def to_string(self) -> str :
        pass

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Type):
            return False
        return self._alpha_equal(value, {}, {})
    
    @abstractmethod
    def _alpha_equal(self, other: "Type", env_self: Dict[str, str], env_other: Dict[str, str]) -> bool :
        pass
    
    