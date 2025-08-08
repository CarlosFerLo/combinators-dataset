import subprocess
import tempfile
from pathlib import Path
import re
from typing import List, Set, Generator
from dataclasses import dataclass
import random
import json
from tqdm import tqdm

FILEPATH = "./combinators/dataset.jsonl"

N = 100000
MAX_DEPTH = 6

BATCH_SIZE = 1000

HEADER = """\
universe u
variable {α β γ : Type u}
def S (f: α → β → γ) (g: α → β) (x: α) : γ := f x (g x)
def K (x: α) (_: β) : α := x
"""


@dataclass
class TypedPair () :
    type: str
    term: str

def generate_combinator(max_depth: int=6) -> str:
        if max_depth == 0:
            return random.choice(['S', 'K'])
        else:
            choice = random.random()
            if choice < 0.3:
                return random.choice(['S', 'K'])
            else:
                left = generate_combinator(max_depth - 1)
                right = generate_combinator(max_depth - 1)
                return f'({left} {right})'
            
def generate_combinator_set(n: int=10000, max_depth: int=6) -> List[str]:
        seen: Set[str] = set()
        while len(seen) < n:
            comb = generate_combinator(max_depth)
            seen.add(comb)
        return list(seen)

def generate_typed_pairs (expressions: List[str]) -> List[TypedPair] :
    
    lean_code = HEADER + "\n".join([ f'#print "[[{expr}]]"\n#check {expr}' for expr in expressions])
    
    with tempfile.TemporaryDirectory() as tmpdir :
        path = Path(tmpdir) / "batch.lean"
        
        path.write_text(lean_code)
        
        result = subprocess.run(
            ["lean", path],
            capture_output=True,
            text=True
        )
        
    statements : List[str] = re.split(r'\[\[.*?\]\]', result.stdout)
    statements = list(map(lambda x : x.strip(), statements))
     
    typed_pairs: List[TypedPair] = []
    
    for statement in statements :
        m = re.match(r'^(?P<term>[SK() ]+?)\s*:\s*(?P<type>.+)$', statement)
        
        if m is not None :
            typed_pairs.append(
                TypedPair(
                    type=m.group("type"),
                    term=m.group("term")
                )
            )
    
    return typed_pairs

def normalize_metavariables(results: List[TypedPair]) -> List[TypedPair]:
    """
    Replace metavariables like ?m.100 with A, B, C... restarting per expression.
    If more than 26 metavariables in an expression, skip it.
    """
    normalized: List[TypedPair] = []
    for entry in results:
        type_str = entry.type
        matches = list(re.finditer(r"\?m\.\d+", type_str))

        # Deduplicate in order of appearance
        meta_vars: List[str] = []
        seen: Set[str] = set()
        for m in matches:
            mv = m.group()
            if mv not in seen:
                seen.add(mv)
                meta_vars.append(mv)

        if len(meta_vars) > 26:
            # Skip if more than A-Z needed
            continue

        replacement_map = {mv: chr(65 + i) for i, mv in enumerate(meta_vars)}
        new_type = type_str
        for mv, rep in replacement_map.items():
            new_type = new_type.replace(mv, rep)
            
        new_type = new_type.replace("\u2192", "->")

        normalized.append(
            TypedPair(
                term=entry.term,
                type=new_type
            )
        )

    return normalized


def batch_iterator(data: List[str], batch_size: int) -> Generator[List[str], None, None]:
    for i in range(0, len(data), batch_size):
        yield data[i:i + batch_size]


def process_expressions (expressions: List[str], batch_size: int = 100) -> Generator[List[TypedPair], None, None] :
    for b in batch_iterator(expressions, batch_size) :
        typed_pairs = generate_typed_pairs(b)
        normalized_pairs = normalize_metavariables(typed_pairs)
        yield normalized_pairs

if __name__ == "__main__" :
    
    print("Generating SK expressions...")
    expressions = generate_combinator_set(N, MAX_DEPTH)
    
    print("Processing SK expressions...")
    with open(FILEPATH, "a", encoding="utf-8") as f :
        for i, batch in tqdm(enumerate(process_expressions(expressions, BATCH_SIZE)), total=N/BATCH_SIZE) :
            for pair in batch:
                    data = {
                        "term": pair.term,  
                        "type": pair.type 
                    }
                    f.write(json.dumps(data) + '\n')
                    
    print("Finished 🎉")