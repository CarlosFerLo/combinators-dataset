from .base import Type
from .variable import TypeVariable

class Arrow (Type) :
    left: Type
    right: Type
    
    def to_string(self) -> str:
        left_str = (
            self.left.to_string()
            if isinstance(self.left, TypeVariable)
            else f"({self.left.to_string()})"
        )
        right_str = self.right.to_string()
        return f"{left_str} -> {right_str}"