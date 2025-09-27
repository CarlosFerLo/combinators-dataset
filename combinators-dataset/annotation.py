from typing import Union, List, Dict
import itertools

# --- SK String Parser -----------------

Node = Union[str, dict]


def _tokenize(expr: str) -> List[str]:
    return expr.replace("(", " ( ").replace(")", " ) ").split()


def parse_sk(expr: str) -> Node:

    tokens = _tokenize(expr)
    if len(tokens) == 0:
        raise ValueError("Empty expression")

    counters = {"S": itertools.count(1), "K": itertools.count(1)}

    def next_name(sym: str) -> str:
        return f"{sym}_{next(counters[sym])}"

    idx = 0
    n = len(tokens)

    def parse_atom() -> Node:
        nonlocal idx
        if idx >= n:
            raise ValueError("Unexpected end of input while parsing atom")

        tok = tokens[idx]
        if tok == "(":
            idx += 1
            node = parse_expr()
            if idx >= n or tokens[idx] != ")":
                raise ValueError("Unmatched '(' or missing ')'")
            idx += 1
            return node
        elif tok in ("S", "K"):
            idx += 1
            return next_name(tok)
        else:
            raise ValueError(f"Unexpected token: {tok!r}")

    def parse_expr() -> Node:
        nonlocal idx

        node = parse_atom()

        while idx < n and tokens[idx] != ")":
            right = parse_atom()
            node = {"left": node, "right": right}

        return node

    result = parse_expr()
    if idx != n:
        raise ValueError(f"Unexpected trailing tokens: {' '.join(tokens[idx:])!r}")
    return result


# ---------- Type System ----------


class TVar:
    _ids = itertools.count()

    def __init__(self, name=None):
        self.id = next(TVar._ids)
        self.name = name or f"t{self.id}"

    def __repr__(self):
        return self.name


class TArrow:
    def __init__(self, left, right):
        self.left = left
        self.right = right

    def __repr__(self):
        return f"({self.left} -> {self.right})"


Type = Union[TVar, TArrow]

# ---------- Unification ----------


def occurs(v: TVar, t: Type) -> bool:
    if isinstance(t, TVar):
        return v.id == t.id
    elif isinstance(t, TArrow):
        return occurs(v, t.left) or occurs(v, t.right)
    return False


Subst = Dict[int, Type]


def apply(subst: Subst, t: Type) -> Type:
    if isinstance(t, TVar):
        if t.id in subst:
            return apply(subst, subst[t.id])
        return t
    elif isinstance(t, TArrow):
        return TArrow(apply(subst, t.left), apply(subst, t.right))
    return t


def unify(t1: Type, t2: Type, subst: Subst):
    t1 = apply(subst, t1)
    t2 = apply(subst, t2)
    if isinstance(t1, TVar):
        if isinstance(t2, TArrow) or t1.id != t2.id:
            if occurs(t1, t2):
                raise TypeError("Occurs check failed")
            subst[t1.id] = t2
    elif isinstance(t2, TVar):
        unify(t2, t1, subst)
    elif isinstance(t1, TArrow) and isinstance(t2, TArrow):
        unify(t1.left, t2.left, subst)
        unify(t1.right, t2.right, subst)
    else:
        raise TypeError(f"Cannot unify {t1} with {t2}")


# ---------- Type Schemas ----------


def fresh_K():
    A, B = TVar("A"), TVar("B")
    return TArrow(A, TArrow(B, A))


def fresh_S():
    A, B, C = TVar("A"), TVar("B"), TVar("C")
    return TArrow(
        TArrow(A, TArrow(B, C)),
        TArrow(TArrow(A, B), TArrow(A, C)),
    )


# ---------- Annotation ----------


def annotate(expr):
    subst: Subst = {}

    def go(node):
        if isinstance(node, str):
            if node.startswith("K"):
                t = fresh_K()
            elif node.startswith("S"):
                t = fresh_S()
            else:
                raise ValueError(f"Unknown leaf {node}")
            return {"sym": node, "type": t}

        # application
        left = go(node["left"])
        right = go(node["right"])
        res_type = TVar()
        unify(left["type"], TArrow(right["type"], res_type), subst)
        return {"left": left, "right": right, "type": res_type}

    tree = go(expr)

    def resolve_types(node):
        node["type"] = apply(subst, node["type"])
        if "left" in node:
            resolve_types(node["left"])
        if "right" in node:
            resolve_types(node["right"])
        return node

    return resolve_types(tree)


# ---------- Example ----------
if __name__ == "__main__":

    expr = parse_sk(input("Enter SK string: "))
    annotated = annotate(expr)

    import pprint

    pprint.pprint(annotated)
