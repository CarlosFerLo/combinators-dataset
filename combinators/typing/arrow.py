from typing import Dict

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
    
    def _alpha_equal(self, other: Type, env_self: Dict[str, str], env_other: Dict[str, str]) -> bool:
        if not isinstance(other, Arrow):
            return False

        return (
            self.left._alpha_equal(other.left, env_self, env_other)
            and self.right._alpha_equal(other.right, env_self, env_other)
        )
