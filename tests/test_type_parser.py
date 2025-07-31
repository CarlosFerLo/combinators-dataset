import combinators
def test_combinators_base_type_has_parse_string_method () :
    assert hasattr(combinators.parsers, "parse_type_expr")

def test_parse_single_variable():
    from combinators.typing import TypeVariable
    from combinators.parsers import parse_type_expr
    
    result = parse_type_expr("A")
    assert isinstance(result, TypeVariable)
    assert result.name == "A"
    assert result.is_arbitrary is True  # default

def test_parse_simple_implication():
    from combinators.typing import TypeVariable, Implication
    from combinators.parsers import parse_type_expr

    result = parse_type_expr("A -> B")
    assert isinstance(result, Implication)
    assert isinstance(result.left, TypeVariable)
    assert isinstance(result.right, TypeVariable)
    assert result.left.name == "A"
    assert result.right.name == "B"

def test_parse_right_associative_implication():
    from combinators.typing import TypeVariable, Implication
    from combinators.parsers import parse_type_expr

    result = parse_type_expr("A -> B -> C")
    assert isinstance(result, Implication)
    assert isinstance(result.left, TypeVariable)
    assert result.left.name == "A"
    assert isinstance(result.right, Implication)
    assert isinstance(result.right.left, TypeVariable)
    assert result.right.left.name == "B"
    assert isinstance(result.right.right, TypeVariable)
    assert result.right.right.name == "C"

def test_parse_parenthesized_implication():
    from combinators.typing import TypeVariable, Implication
    from combinators.parsers import parse_type_expr

    result = parse_type_expr("(A -> B) -> C")
    assert isinstance(result, Implication)
    assert isinstance(result.left, Implication)
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
    
def test_implication_with_non_arbitrary_variable():
    from combinators.typing import Implication, TypeVariable
    from combinators.parsers import parse_type_expr

    result = parse_type_expr("_A -> B")

    assert isinstance(result, Implication)
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