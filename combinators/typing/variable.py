from .base import Type
from typing import Dict

class TypeVariable (Type) :
    name: str
    is_arbitrary: bool = True
    
    def to_string(self) -> str:
        return self.name if self.is_arbitrary else f"_{self.name}"
    
    def _alpha_equal(self, other: Type, env_self: Dict[str, str], env_other: Dict[str, str]) -> bool:
        if not isinstance(other, TypeVariable):
            return False
        if self.is_arbitrary != other.is_arbitrary:
            return False

        name1 = self.name
        name2 = other.name

        if name1 in env_self:
            return env_self[name1] == name2
        if name2 in env_other:
            return False  # other already assigned but self not

        # assign both ways
        env_self[name1] = name2
        env_other[name2] = name1
        return True