from pathlib import Path
from typing import List, Tuple, Iterable
import tempfile
import logging
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(threadName)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

DATASET_DIR = Path("combinators-dataset/dataset")
BATCH_SIZE = 1000

TypedPairs = List[Tuple[Tuple[str, str]]]


def load_dataset(path: Path) -> TypedPairs:
    return []


def batch_iterator(dataset: TypedPairs, batch_size: int) -> Iterable[TypedPairs]:
    for i in range(0, len(dataset), batch_size):
        yield dataset[i : i + batch_size]


def validate(dataset: TypedPairs) -> Tuple[TypedPairs, TypedPairs]:
    return ([], [])


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
