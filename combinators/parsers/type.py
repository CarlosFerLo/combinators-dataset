from typing import List, Tuple
import re

from ..typing import Type, TypeVariable, Arrow

def parse_type_expr(string: str) -> Type:
        tokens = _tokenize(string)
        type_expr, remaining = _parse_expr(tokens)
        if remaining:
            raise ValueError(f"Unexpected tokens after parsing: {remaining}")
        return type_expr


def _tokenize(string: str) -> List[str]:
    token_pattern = r"\w+|->|\(|\)"
    return re.findall(token_pattern, string)


def _parse_expr(tokens: List[str]) -> Tuple[Type, List[str]]:
    left, tokens = _parse_simple_type(tokens)

    if tokens and tokens[0] == "->":
        tokens = tokens[1:]  # consume '->'
        right, tokens = _parse_expr(tokens)
        return Arrow(left=left, right=right), tokens
    else:
        return left, tokens


def _parse_simple_type(tokens: List[str]) -> Tuple[Type, List[str]]:
    if not tokens:
        raise ValueError("Unexpected end of input")

    token = tokens.pop(0)

    if token == "(":
        inner, tokens = _parse_expr(tokens)
        if not tokens or tokens.pop(0) != ")":
            raise ValueError("Expected ')'")
        return inner, tokens

    elif re.match(r"\w+", token):
        is_arbitrary = not token.startswith("_")
        name = token.lstrip("_")
        return TypeVariable(name=name, is_arbitrary=is_arbitrary), tokens

    else:
        raise ValueError(f"Unexpected token: {token}")