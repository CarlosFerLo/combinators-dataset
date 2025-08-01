from typing import List, Callable, Type, Dict

from ..combinator import Combinator, S, K

def build_combinator_parser(combinators: List[Type[Combinator]]) -> Callable[[str], Combinator]:
    symbol_table: Dict[str, Type[Combinator]] = {cls.__name__: cls for cls in combinators}

    def parse_expr(chars: List[str]) -> Combinator:
        stack: List[Combinator] = []

        def next_token():
            if not chars:
                raise ValueError("Unexpected end of input.")
            return chars.pop(0)

        def parse_atom() -> Combinator:
            token = next_token()

            if token == '(':
                expr = parse_expr(chars)
                if not chars or chars.pop(0) != ')':
                    raise ValueError("Mismatched parentheses")
                return expr
            elif token in symbol_table:
                return symbol_table[token]()
            else:
                raise KeyError(f"Unknown combinator symbol: '{token}'")

        # Left-associative application
        while chars:
            if chars[0] == ')':
                break  # End of current expression
            term = parse_atom()
            while stack and len(stack[-1].args) < stack[-1].arity:
                stack[-1].args.append(term)
                break
            else:
                stack.append(term)

        if not stack:
            raise ValueError("Empty expression or unmatched parentheses")

        # Final reduction if possible
        while len(stack) > 1:
            func = stack[-2]
            arg = stack[-1]
            if len(func.args) < func.arity:
                func.args.append(arg)
                stack.pop()
            else:
                break

        if len(stack) != 1:
            raise ValueError("Could not reduce expression to a single combinator")

        return stack[0]

    def parser(source: str) -> Combinator:
        chars = list(source.replace(" ", ""))
        result = parse_expr(chars)
        if chars:
            raise ValueError("Unexpected characters after parsing.")
        return result

    return parser

sk_parser = build_combinator_parser([S, K])