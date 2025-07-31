from pydantic import BaseModel
from abc import ABC, abstractmethod
from typing import List, Optional, Type

from .typing import Type as _Type

class Combinator (BaseModel, ABC) :
    
    args: List["Combinator"] = []
    
    @staticmethod
    @abstractmethod
    def type_schema () -> _Type :
        pass
    
    @staticmethod
    def from_schema (schema: _Type, name: Optional[str] = None) -> Type["Combinator"] :
        class NewCombinator (Combinator) :
            @staticmethod
            def type_schema() -> _Type:
                return schema
            
        if name :
            NewCombinator.__name__ = name
            
        return NewCombinator
    
    