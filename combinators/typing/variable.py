from .base import Type

class TypeVariable (Type) :
    name: str
    is_arbitrary: bool = True
    
    def to_string(self) -> str:
        return self.name if self.is_arbitrary else f"_{self.name}"