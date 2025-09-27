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
BATCH_SIZE = 10

LEAN_HEADER = """universe u
variable {α β γ : Type u}
def s (f: α → β → γ) (g: α → β) (x: α) : γ := f x (g x)
def k (x: α) (_: β) : α := x

variable { A B C D E F G H I J L M N O P Q R T U V W X Y Z : Type u }
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

    tmp = tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", suffix=".lean", delete=False
    )

    try:

        tmp.write(LEAN_HEADER)

        for pair in batch:
            tmp.write(f"#check ( {pair[1].lower()} : {pair[0]} )\n")

        with open(tmp.name, "r") as f:
            logging.info("LEAN FILE:" + f.read())

        results = subprocess.run(
            ["lean", "--json", tmp.name], capture_output=True, text=True
        )

        output: List[Dict[str, Union[str, int]]] = []
        for line in results.stdout.splitlines():

            if line.strip():
                out = json.loads(line)
                output.append(out)

        valid_pairs: TypedPairs = []
        invalid_pairs: TypedPairs = []

        for out, pair in zip(output, batch):
            if out["severity"] == "error":
                invalid_pairs.append(pair)
            else:
                valid_pairs.append(pair)

    finally:
        tmp.close()
        if os.path.exists(tmp.name):
            os.remove(tmp.name)

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
