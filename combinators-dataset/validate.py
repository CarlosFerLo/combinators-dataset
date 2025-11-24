from pathlib import Path
from typing import List, Tuple, Iterable, Dict, Union
import tempfile
import logging
import subprocess
from tqdm import tqdm
import json
import os

from .utils import dump_jsonl

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(threadName)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

DATASET_DIR = Path("combinators-dataset/dataset")
BATCH_SIZE = 100

LEAN_HEADER = (
    LEAN_HEADER
) = """
import Lean
open Lean Elab Command Meta Term

universe u
variable {α β γ : Type u}
def s (f: α → β → γ) (g: α → β) (x: α) : γ := f x (g x)
def k (x: α) (_: β) : α := x

-- Declare type variables as axioms so they're in scope everywhere
axiom A : Type u
axiom B : Type u
axiom C : Type u
axiom D : Type u
axiom E : Type u
axiom F : Type u
axiom G : Type u
axiom H : Type u
axiom I : Type u
axiom J : Type u
axiom L : Type u
axiom M : Type u
axiom N : Type u
axiom O : Type u
axiom P : Type u
axiom Q : Type u
axiom R : Type u
axiom T : Type u
axiom U : Type u
axiom V : Type u
axiom W : Type u
axiom X : Type u
axiom Y : Type u
axiom Z : Type u

syntax (name := checkStr) "#check_str" str str : command

@[command_elab checkStr]
def elabCheckStr : CommandElab := fun stx => do
  try
    -- Extract the two literal strings
    let some tyStr   := stx[1].isStrLit? | throwError "expected first argument to be a string literal"
    let some termStr := stx[2].isStrLit? | throwError "expected second argument to be a string literal"

    -- Parse the strings into Syntax; runParserCategory returns Except
    let tyStx ← match Parser.runParserCategory (← getEnv) `term tyStr with
      | .ok stx  => pure stx
      | .error e => throwError "parse type failed: {e}"

    let termStx ← match Parser.runParserCategory (← getEnv) `term termStr with
      | .ok stx  => pure stx
      | .error e => throwError "parse term failed: {e}"

    -- Elaborate inside TermElabM
    let ok ← liftTermElabM do
      let expectedTy ← elabType tyStx
      -- Elaborate the term WITHOUT an expected type to get its true inferred type
      let termExpr ← elabTerm termStx none
      let actualTy ← inferType termExpr
      -- Check if the types are definitionally equal
      isDefEq actualTy expectedTy

    if ok then
      logInfo m!"✅ {termStr} : {tyStr}"
    else
      logInfo m!"❌ {termStr} : {tyStr} (type mismatch)"
  catch err =>
    -- Catch any error and print ❌ instead of failing
    let termStr := stx[2].isStrLit?.getD "<unknown term>"
    let tyStr   := stx[1].isStrLit?.getD "<unknown type>"
    logInfo m!"❌ {termStr} : {tyStr} — {← err.toMessageData.toString}"
  pure ()

"""

TypedPairs = List[Tuple[str, str]]


def load_dataset(path: Path) -> TypedPairs:
    pairs: TypedPairs = []

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():

                data = json.loads(line)

                missing_keys = []
                if "type" not in data:
                    missing_keys.append("type")
                if "term" not in data:
                    missing_keys.append("term")

                if missing_keys:
                    raise ValueError(
                        f"The file '{path}' isn't well formed, contains a line with missing keys: "
                        + ", ".join(missing_keys)
                    )

                pairs.append((data["type"], data["term"]))

    return pairs


def batch_iterator(dataset: TypedPairs, batch_size: int) -> Iterable[TypedPairs]:
    for i in range(0, len(dataset), batch_size):
        yield dataset[i : i + batch_size]


def validate(batch: TypedPairs) -> Tuple[TypedPairs, TypedPairs]:

    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", suffix=".lean", delete=False
    ) as tmp:
        tmp.write(LEAN_HEADER)

        # write pairs as: #check_str "<type>" "<term>"
        for pair in batch:
            tmp.write(f'#check_str "{pair[0]}"  "{pair[1].lower()}"\n')
    try:

        results = subprocess.run(
            ["lean", "--json", tmp.name],
            capture_output=True,
            text=True,
            timeout=60,
        )

        output = results.stdout + "\n" + results.stderr

        logging.debug(f"Lean output:\n{output}")

        val: List[bool] = []
        for line in output.splitlines():

            line = line.strip()
            if not line:
                continue

            try:
                msg = json.loads(line)
                if msg.get("severity") == "information":

                    text = msg["data"].strip()

                    if text.startswith("✅"):
                        val.append(True)
                    elif text.startswith("❌"):
                        val.append(False)
            except json.JSONDecodeError:
                continue

    finally:
        tmp.close()
        if os.path.exists(tmp.name):
            os.remove(tmp.name)

    assert len(batch) == len(val)

    valid_pairs: TypedPairs = []
    invalid_pairs: TypedPairs = []

    for pair, ok in zip(batch, val):
        if ok:
            valid_pairs.append(pair)
        else:
            invalid_pairs.append(pair)

    return (valid_pairs, invalid_pairs)


if __name__ == "__main__":

    for partition in ["train", "validation", "test"]:
        logging.info(f"Starting validation of {partition} set...")

        dataset_path = DATASET_DIR / f"{partition}.jsonl"

        logging.info(f"Loading partition from '{dataset_path}'...")

        dataset = load_dataset(dataset_path)

        logging.info(f"✅ Partition loaded successfully. (examples: {len(dataset)})")

        valid_pairs: TypedPairs = []
        invalid_pairs: TypedPairs = []

        iterator = tqdm(
            batch_iterator(dataset, BATCH_SIZE),
            total=(len(dataset) + BATCH_SIZE - 1) // BATCH_SIZE,
        )

        for batch in iterator:

            new_valid_pairs, new_invalid_pairs = validate(batch)

            valid_pairs.extend(new_valid_pairs)
            invalid_pairs.extend(new_invalid_pairs)

            iterator.set_postfix(
                {"valid": len(valid_pairs), "invalid": len(invalid_pairs)}
            )

        if invalid_pairs:
            logging.warning(f"⚠️ Invalid Pairs found ⚠️ (count: {len(invalid_pairs)})")

            logging.info(
                f"Dumping invalid pairs into '{DATASET_DIR / 'invalid_pairs.jsonl'}'"
            )

            dump_jsonl(DATASET_DIR / "invalid_pairs.jsonl", invalid_pairs)

            logging.info(f"Removing old '{dataset_path}' file.")

            dataset_path.unlink()

            logging.info(f"Dumping valid pairs into new '{dataset_path}.jsonl'")

            dump_jsonl(dataset_path, valid_pairs)

            logging.info("✅ Pairs written successfully.")

        else:
            logging.info(f"✅ Validation of {partition} passed without exceptions.")
