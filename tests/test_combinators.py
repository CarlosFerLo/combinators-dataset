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
    from combinators.typing import Type
    
    assert hasattr(combinators.Combinator, "from_schema")
    
    schema = Type()
    name = "C"
    
    c = combinators.Combinator.from_schema(schema, name)
    
    assert c.__name__ == name
    assert c.type_schema() == schema
 
# TODO: from_string method
    
def test_combinators_combinator_has_expected_properties () :
    """Expected Properties:
        - args [Combinator] : list of combinators as arguments (Default: [])
    """
    
    from combinators.typing import Type
    
    class SampleCombinator (combinators.Combinator) :
        @staticmethod
        def type_schema() -> Type:
            return Type()
    
    c1 = SampleCombinator()
    c2 = SampleCombinator()
    
    c3 = SampleCombinator(args=[c1, c2])
    
    assert c1.args == []
    assert c2.args == []
    assert c3.args == [c1, c2]
    
