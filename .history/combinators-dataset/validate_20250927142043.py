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


def load_dataset(path: Path) -> List[Tuple[str, str]]:
    return []


def batch_iterator(
    dataset: List[Tuple[str, str]], batch_size: int
) -> Iterable[List[Tuple[str, str]]]:
    for i in range(0, len(dataset), batch_size):
        yield dataset[i : i + batch_size]


def validate(dataset: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    return []


if __name__ == "__main__":

    for partition in ["train", "validation", "test"]:
        logging.info(f"Starting validation of {partition} set...")

        dataset_path = DATASET_DIR / f"{partition}.jsonl"

        logging.info(f"Loading partition from '{dataset_path}'...")

        dataset = load_dataset(dataset_path)

        logging.info(f"✅ Partition loaded successfully. (examples: {len(dataset)})")

        for batch in tqdm(
            batch_iterator(dataset, BATCH_SIZE),
            total=(len(dataset) + BATCH_SIZE - 1) // BATCH_SIZE,
        ):
            pass
