import pytest
import combinators

import pydantic

def test_combinators_has_typing_module () :
    assert hasattr(combinators, "typing")

def test_combinators_has_base_type () :
    assert hasattr(combinators.typing, "Type")
    
def test_combinators_base_type_is_pydantic_base_module () :
    assert issubclass(combinators.typing.Type, pydantic.BaseModel)