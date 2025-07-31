from pydantic import BaseModel, field_validator
from abc import ABC, abstractmethod
from typing import List, Optional, Type, ClassVar

from .typing import Type as _Type, Arrow
from .parsers import parse_type_expr

class Combinator (BaseModel, ABC) :
    
    arity: ClassVar[int]
    args: List["Combinator"] = []
    
    def __init_subclass__(cls):
        if 'arity' not in cls.__dict__:
            raise TypeError(f"{cls.__name__} must define 'arity'")
        
    @field_validator("args")
    def check_args_length_not_bigger_than_arity (cls, args: List["Combinator"]) :
        if len(args) > cls.arity :
            raise ValueError(f"The number of arguments cannot be bigger than the arity.\nNumber of arguments: {len(args)}\nArity: {cls.arity}")
        return args
    
    @staticmethod
    @abstractmethod
    def type_schema () -> _Type :
        pass
    
    @staticmethod
    def from_schema (schema: _Type, name: Optional[str] = None) -> Type["Combinator"] :
        
        arity_ = Combinator._get_args(schema)
        class NewCombinator (Combinator) :
            arity: ClassVar[int] = arity_
            @staticmethod
            def type_schema() -> _Type:
                return schema
            
        if name :
            NewCombinator.__name__ = name
            
        return NewCombinator
    
    @staticmethod
    def from_string(string: str, name: Optional[str] = None) -> Type["Combinator"] :
        schema = parse_type_expr(string)
        
        return Combinator.from_schema(schema, name)
    
    @staticmethod
    def _get_args (schema: _Type) -> int :
        arity = 0
        while isinstance(schema, Arrow) :
            arity += 1
            schema = schema.right
            
        return arity
