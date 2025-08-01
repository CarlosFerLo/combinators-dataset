import combinators
import pytest

from typing import Tuple

def test_combinators_has_combinator () :
    assert hasattr(combinators, "Combinator")
    
def test_combinators_combinator_is_pydantic_base_model () :
    
    import pydantic 
    
    assert issubclass(combinators.Combinator, pydantic.BaseModel)

def test_combinators_combinator_has_type_schema_abstract_method () :
    import abc
    assert issubclass(combinators.Combinator, abc.ABC)
    assert "type_schema" in combinators.Combinator.__abstractmethods__
    
def test_combinators_combinator_metaclass_has_from_schema_method () :
    from combinators.typing import TypeVariable
    
    assert hasattr(combinators.Combinator, "from_schema")
    
    schema = TypeVariable(name="A")
    name = "C"
    
    c = combinators.Combinator.from_schema(schema, name)
    
    assert c.__name__ == name
    assert c.type_schema() == schema
 
def test_combinators_combinator_metaclass_hass_from_string_method () :
    
    from combinators.parsers import parse_type_expr
    
    assert hasattr(combinators.Combinator, "from_string")
    
    schema_string = "A -> B -> A"
    schema = parse_type_expr(schema_string)
    
    name = "K"
    
    K = combinators.Combinator.from_string(schema_string, name)
    
    assert K.__name__ == name
    assert K.type_schema() == schema
    
def test_combinators_combinator_subclasses_fail_if_no_arity () :
    
    from combinators.typing import Type, TypeVariable
    
    with pytest.raises(TypeError) :
        class SampleCombinator (combinators.Combinator) : # type: ignore
            @staticmethod
            def type_schema() -> Type:
                return TypeVariable(name="A")

@pytest.mark.parametrize("schema", [
    ["A", 0],
    ["_X", 0],
    ["A -> B", 1],
    ["A -> B -> C", 2],
    ["(A -> B) -> C", 1],
    ["((A -> B) -> C) -> D", 1],
    ["_X -> _Y -> Z", 2],
    ["(_X -> (_Y -> Z)) -> A", 1],
])
def test_combinators_combinator_from_schema_calculates_correct_arg_max (schema: Tuple[str, int]) :
    SampleCombinator = combinators.Combinator.from_string(schema[0], "SampleCombinator")
    
    assert SampleCombinator.arity == schema[1]

def test_combinators_combinator_has_expected_properties () :
    """Expected Properties:
        - args [Combinator] : list of combinators as arguments (Default: [])
    """
    
    SampleCombinator = combinators.Combinator.from_string("A -> B -> C")
    
    c1 = SampleCombinator()
    c2 = SampleCombinator()
    
    c3 = SampleCombinator(args=[c1, c2])
    
    assert c1.args == []
    assert c2.args == []
    assert c3.args == [c1, c2]
    
@pytest.mark.parametrize("input", [
    ["A", 1],
    ["A -> B", 3],
    ["A -> B -> C", 5],
    ["(A -> B) -> C", 2],
])
def test_combinators_combinator_raises_validation_error_if_try_to_init_with_to_many_args (input: Tuple[str, int]) :
    
    import pydantic
    
    base_combinator = combinators.Combinator.from_string("A")
    sample_combinator = combinators.Combinator.from_string(input[0])
    
    args = [ base_combinator() ] * input[1]
    
    with pytest.raises(pydantic.ValidationError) :
        sample_combinator(args=args)
        
def test_combinators_has_combinators_K_and_S () :
    assert hasattr(combinators, "K")
    assert hasattr(combinators, "S")
    
    assert issubclass(combinators.K, combinators.Combinator)
    assert issubclass(combinators.S, combinators.Combinator)
    
    assert combinators.K.__name__ == "K"
    assert combinators.S.__name__ == "S"
    
    assert combinators.K.type_schema().to_string() == "A -> B -> A"
    assert combinators.S.type_schema().to_string() == "(A -> B -> C) -> (A -> B) -> A -> C"
    
    assert combinators.K.arity == 2
    assert combinators.S.arity == 3
    
def test_combinators_combinator_has_get_type_label_method () :
    assert hasattr(combinators.Combinator, "get_type_label")
    
""" TODO:
@pytest.mark.parametrize("expr", ["S", "K"])
def test_combinator_combinator_get_type_label_method_on_simple_cases (expr: str) :
    
    from combinators.parsers import sk_parser, parse_type_expr
    
    C = sk_parser(expr)
    assert C.get_type_label() == parse_type_expr("")
"""