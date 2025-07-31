import combinators
import pytest

def test_combinators_has_typing_module () :
    assert hasattr(combinators, "typing")

# --- Base Type --------------------------------------
def test_combinators_has_base_type () :
    assert hasattr(combinators.typing, "Type")
    
def test_combinators_base_type_is_pydantic_base_model () :
    
    import pydantic
    
    assert issubclass(combinators.typing.Type, pydantic.BaseModel)
    
def test_combinators_base_type_has_to_string_abstract_method () :
    
    import abc
    
    assert issubclass(combinators.typing.Type, abc.ABC)
    assert "to_string" in combinators.typing.Type.__abstractmethods__
    
# --- Type Variable -----------------------------------
    
def test_combinator_has_type_variable () :
    assert hasattr(combinators.typing, "TypeVariable")
    
def test_combinator_type_variable_is_subclass_of_base_type () :
    assert issubclass(combinators.typing.TypeVariable, combinators.typing.Type)
    
def test_combinator_type_variable_has_expected_properties () :
    """ Expected Properties:
        - name [str] : unique identifier string
        - is_arbitrary [bool] : true if it is an arbitrary type variable
    """
    
    from combinators.typing import TypeVariable
    
    var = TypeVariable(name="A", is_arbitrary=False)
    
    assert var.name == "A"
    assert var.is_arbitrary == False
    
def test_combinator_type_variable_has_default_is_arbitrary_true () :
    from combinators.typing import TypeVariable
    
    var = TypeVariable(name = "B")
    
    assert var.name == "B"
    assert var.is_arbitrary == True
    
# --- Arrow ----------------------------------------

def test_combinators_has_arrow () :
    assert hasattr(combinators.typing, "Arrow")
    
def test_combinators_arrow_is_a_subclass_of_base_type () :
    assert issubclass(combinators.typing.Arrow, combinators.typing.Type)
    
def test_combinators_arrow_has_expected_properties () :
    """Expected Properties:
        - left [Type] : type at the left
        - right [Type] : type at the right
    """
    
    from combinators.typing import TypeVariable, Arrow
    
    A = TypeVariable(name="A")
    B = TypeVariable(name="B")
    
    imp = Arrow(left=A, right=B)
    
    assert imp.left == A
    assert imp.right == B
    
# --- Dumping to String -------------------------------------

@pytest.mark.parametrize("expr", [
    "A",
    "_X",
    "A -> B",
    "A -> B -> C",
    "(A -> B) -> C",
    "((A -> B) -> C) -> D",
    "_X -> _Y -> Z",
    "(_X -> (_Y -> Z)) -> A",
])
def test_round_trip(expr: str):
    from combinators.parsers import parse_type_expr
    
    parsed = parse_type_expr(expr)
    dumped = parsed.to_string()
    reparsed = parse_type_expr(dumped)
    assert reparsed == parsed, f"Expected {parsed} == {reparsed}"