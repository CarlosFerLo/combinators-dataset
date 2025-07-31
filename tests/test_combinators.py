import combinators

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

def test_combinators_combinator_has_expected_properties () :
    """Expected Properties:
        - args [Combinator] : list of combinators as arguments (Default: [])
    """
    
    from combinators.typing import TypeVariable
    
    SampleCombinator = combinators.Combinator.from_schema(TypeVariable(name="A"))
    
    c1 = SampleCombinator()
    c2 = SampleCombinator()
    
    c3 = SampleCombinator(args=[c1, c2])
    
    assert c1.args == []
    assert c2.args == []
    assert c3.args == [c1, c2]
    
