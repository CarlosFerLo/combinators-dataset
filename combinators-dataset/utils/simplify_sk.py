def simplify_sk(expr: str) -> str:
    """
    Simplify an SK combinator expression by removing redundant parentheses,
    assuming left-associative application.
    """
    tokens = [ch for ch in expr if ch in "SK()"]

    # --- Recursive descent parser ---
    def parse(tokens):
        def parse_atom():
            t = tokens.pop(0)
            if t in "SK":
                return t
            elif t == "(":
                e = parse(tokens)
                assert tokens.pop(0) == ")"
                return e
            else:
                raise ValueError("Unexpected token: " + t)

        exprs = []
        while tokens and tokens[0] != ")":
            exprs.append(parse_atom())
        # Left-associative application: fold left
        e = exprs[0]
        for arg in exprs[1:]:
            e = (e, arg)
        return e

    ast = parse(tokens)

    # --- Pretty printer with minimal parentheses ---
    def pretty_print(e):
        if isinstance(e, str):
            return e
        f, a = e
        left = pretty_print(f)
        right = pretty_print(a)
        # Parenthesize the right argument if it’s an application
        if isinstance(a, tuple):
            right = f"({right})"
        return f"{left} {right}"

    return pretty_print(ast)
