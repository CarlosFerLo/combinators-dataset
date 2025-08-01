import combinators
import pytest

def test_combinators_parsers_has_parse_type_expr () :
    assert hasattr(combinators.parsers, "parse_type_expr")

def test_parse_single_variable():
    from combinators.typing import TypeVariable
    from combinators.parsers import parse_type_expr
    
    result = parse_type_expr("A")
    assert isinstance(result, TypeVariable)
    assert result.name == "A"
    assert result.is_arbitrary is True  # default

def test_parse_simple_arrow():
    from combinators.typing import TypeVariable, Arrow
    from combinators.parsers import parse_type_expr

    result = parse_type_expr("A -> B")
    assert isinstance(result, Arrow)
    assert isinstance(result.left, TypeVariable)
    assert isinstance(result.right, TypeVariable)
    assert result.left.name == "A"
    assert result.right.name == "B"

def test_parse_right_associative_arrow():
    from combinators.typing import TypeVariable, Arrow
    from combinators.parsers import parse_type_expr

    result = parse_type_expr("A -> B -> C")
    assert isinstance(result, Arrow)
    assert isinstance(result.left, TypeVariable)
    assert result.left.name == "A"
    assert isinstance(result.right, Arrow)
    assert isinstance(result.right.left, TypeVariable)
    assert result.right.left.name == "B"
    assert isinstance(result.right.right, TypeVariable)
    assert result.right.right.name == "C"

def test_parse_parenthesized_arrow():
    from combinators.typing import TypeVariable, Arrow
    from combinators.parsers import parse_type_expr

    result = parse_type_expr("(A -> B) -> C")
    assert isinstance(result, Arrow)
    assert isinstance(result.left, Arrow)
    assert isinstance(result.left.left, TypeVariable)
    assert result.left.left.name == "A"
    assert isinstance(result.left.right, TypeVariable)
    assert result.left.right.name == "B"
    assert isinstance(result.right, TypeVariable)
    assert result.right.name == "C"
    
def test_parse_simple_non_arbitrary_variable():
    from combinators.typing import TypeVariable
    from combinators.parsers import parse_type_expr

    result = parse_type_expr("_A")
    assert isinstance(result, TypeVariable)
    assert result.name == "A"
    assert result.is_arbitrary is False
    
def test_arrow_with_non_arbitrary_variable():
    from combinators.typing import Arrow, TypeVariable
    from combinators.parsers import parse_type_expr

    result = parse_type_expr("_A -> B")

    assert isinstance(result, Arrow)
    assert isinstance(result.left, TypeVariable)
    assert result.left.name == "A"
    assert result.left.is_arbitrary is False
    assert isinstance(result.right, TypeVariable)
    assert result.right.name == "B"
    assert result.right.is_arbitrary is True
    
def test_parenthesized_non_arbitrary_variable():
    from combinators.typing import TypeVariable
    from combinators.parsers import parse_type_expr

    result = parse_type_expr("(_A)")
    assert isinstance(result, TypeVariable)
    assert result.name == "A"
    assert result.is_arbitrary is False
    
def test_parse_empty_string_fails():
    from combinators.parsers import parse_type_expr
    
    with pytest.raises(ValueError):
        parse_type_expr("")

def test_unmatched_parens():
    from combinators.parsers import parse_type_expr
    
    with pytest.raises(ValueError):
        parse_type_expr("(A -> B")

def test_double_arrow_error():
    from combinators.parsers import parse_type_expr
    
    with pytest.raises(ValueError):
        parse_type_expr("A -> -> B")