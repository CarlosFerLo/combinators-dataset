from .base import Type

class TypeVariable (Type) :
    name: str
    is_arbitrary: bool = True