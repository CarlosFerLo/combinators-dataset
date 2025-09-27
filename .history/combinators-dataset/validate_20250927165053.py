from pathlib import Path
from typing import List, Tuple, Iterable
import tempfile
import logging
from tqdm import tqdm
import json
from .utils import dump_jsonl

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(threadName)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

DATASET_DIR = Path("combinators-dataset/dataset")
BATCH_SIZE = 1000

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

    tmp = tempfile.TemporaryFile("w", encoding="utf-8")

    # TODO


if __name__ == "__main__":

    for partition in ["train", "validation", "test"]:
        logging.info(f"Starting validation of {partition} set...")

        dataset_path = DATASET_DIR / f"{partition}.jsonl"

        logging.info(f"Loading partition from '{dataset_path}'...")

        dataset = load_dataset(dataset_path)

        logging.info(f"✅ Partition loaded successfully. (examples: {len(dataset)})")

        valid_pairs: TypedPairs = []
        invalid_pairs: TypedPairs = []

        for i, batch in enumerate(
            tqdm(
                batch_iterator(dataset, BATCH_SIZE),
                total=(len(dataset) + BATCH_SIZE - 1) // BATCH_SIZE,
            )
        ):

            new_valid_pairs, new_invalid_pairs = validate(batch)

            tqdm.write(
                f"[batch {i+1}] Results: {len(new_valid_pairs)} valid / {len(new_invalid_pairs)} invalid"
            )

            valid_pairs.extend(new_valid_pairs)
            invalid_pairs.extend(new_invalid_pairs)

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
