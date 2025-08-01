import combinators
import pytest

def test_combinators_parsers_has_build_combinator_parser () :
    assert hasattr(combinators.parsers, "build_combinator_parser")
    
def test_single_combinator_K():
    
    from combinators.parsers import build_combinator_parser
    from combinators import K
    
    parser = build_combinator_parser([K])
    k_instance = parser("K")
    assert isinstance(k_instance, K)
    assert k_instance.args == []
    
def test_single_combinator_S():
    
    from combinators.parsers import build_combinator_parser
    from combinators import S
    
    parser = build_combinator_parser([S])
    s_instance = parser("S")
    assert isinstance(s_instance, S)
    assert s_instance.args == []

def test_combinator_application_S_K():
    
    from combinators.parsers import build_combinator_parser
    from combinators import S, K
    
    parser = build_combinator_parser([S, K])
    result = parser("SKK")
    
    assert isinstance(result, S)
    assert len(result.args) == 2
    assert isinstance(result.args[0], K)
    assert isinstance(result.args[1], K)
    
    assert result.args[0].args == []
    assert result.args[1].args == []
    
def test_explicit_application():
    
    from combinators.parsers import build_combinator_parser
    from combinators import S, K

    parser = build_combinator_parser([S, K])
    result = parser("S(K)(K)")
    assert isinstance(result, S)
    assert isinstance(result.args[0], K)
    assert isinstance(result.args[1], K)

def test_nested_application():
    
    from combinators.parsers import build_combinator_parser
    from combinators import S, K
    
    parser = build_combinator_parser([S, K])
    result = parser("S(KK)")
    assert isinstance(result, S)
    assert isinstance(result.args[0], K)
    nested = result.args[0].args[0]
    assert isinstance(nested, K)
    

def test_application_with_nested_parentheses():
    
    from combinators.parsers import build_combinator_parser
    from combinators import S, K
    
    parser = build_combinator_parser([S, K])
    result = parser("S(K)(S(K)(K))")
    assert isinstance(result, S)
    assert isinstance(result.args[0], K)
    inner = result.args[1]
    assert isinstance(inner, S)
    assert isinstance(inner.args[0], K)
    assert isinstance(inner.args[1], K)
    
@pytest.mark.parametrize("expr", [
    "S(K", # Missing closing paren
    "SS)", # Missing opening paren
    "S()"  # Missing content between paren 
])
def test_malformed_expression(expr: str):
    
    from combinators.parsers import build_combinator_parser
    from combinators import S, K
    
    parser = build_combinator_parser([S, K])
    with pytest.raises(ValueError):
        parser(expr)  

def test_unknown_combinator():
    
    from combinators.parsers import build_combinator_parser
    from combinators import S, K
    
    parser = build_combinator_parser([S, K])
    
    with pytest.raises(KeyError):
        parser("X")  # 'X' not defined as a combinator

def test_empty_string():
    
    from combinators.parsers import build_combinator_parser
    from combinators import S, K
    
    parser = build_combinator_parser([S, K])
    with pytest.raises(ValueError):
        parser("")

def test_combinators_parsers_has_sk_parser () :
    assert hasattr(combinators.parsers, "sk_parser")