from pydantic import BaseModel
from abc import ABC, abstractmethod
class Type (BaseModel, ABC) :
    """
    Base class for types. All types should inherit from this class.
    """
    
    @abstractmethod
    def to_string(self) -> str :
        pass
    
    