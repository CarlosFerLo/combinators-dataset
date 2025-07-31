import combinators

import pydantic

def test_combinators_has_typing_module () :
    assert hasattr(combinators, "typing")

# --- Base Type --------------------------------------
def test_combinators_has_base_type () :
    assert hasattr(combinators.typing, "Type")
    
def test_combinators_base_type_is_pydantic_base_module () :
    assert issubclass(combinators.typing.Type, pydantic.BaseModel)
    
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
    
# --- Implication ----------------------------------------

def test_combinators_has_implication () :
    assert hasattr(combinators.typing, "Implication")
    
def test_combinators_implication_is_a_subclass_of_base_type () :
    assert issubclass(combinators.typing.Implication, combinators.typing.Type)
    
def test_combinators_implication_has_expected_properties () :
    """Expected Properties:
        - left [Type] : type at the left
        - right [Type] : type at the right
    """
    
    from combinators.typing import TypeVariable, Implication
    
    A = TypeVariable(name="A")
    B = TypeVariable(name="B")
    
    imp = Implication(left=A, right=B)
    
    assert imp.left == A
    assert imp.right == B