def simplify_type(expr: str) -> str:
    """
    Simplify type expressions with arrows, assuming '->' is right-associative.
    Example: ((A -> B) -> C) -> D  -> ((A -> B) -> C) -> D
             A -> (B -> C)        -> A -> B -> C
    """
    # Tokenize
    tokens = []
    i = 0
    while i < len(expr):
        if expr[i].isspace():
            i += 1
            continue
        if expr.startswith("->", i):
            tokens.append("->")
            i += 2
        elif expr[i] in "()":
            tokens.append(expr[i])
            i += 1
        else:
            # Parse variable names (A, B, Maybe Int, etc.)
            j = i
            while j < len(expr) and expr[j] not in "() \t\n\r-":
                j += 1
            tokens.append(expr[i:j])
            i = j

    def parse(tokens):
        def parse_atom():
            t = tokens.pop(0)
            if t == "(":
                e = parse(tokens)
                assert tokens.pop(0) == ")"
                return e
            else:
                return t

        lhs = parse_atom()
        if tokens and tokens[0] == "->":
            tokens.pop(0)
            rhs = parse(tokens)
            return (lhs, "->", rhs)
        return lhs

    def show(e):
        if isinstance(e, str):
            return e
        lhs, _, rhs = e
        left = show(lhs)
        right = show(rhs)
        # Parenthesize left side if it’s an arrow itself
        if isinstance(lhs, tuple):
            left = f"({left})"
        return f"{left} -> {right}"

    return show(parse(tokens))
