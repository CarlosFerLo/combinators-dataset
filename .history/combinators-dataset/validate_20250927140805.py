from pathlib import Path
from typing import List, Tuple
import tempfile
import logging

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(threadName)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

DATASET_DIR = Path("combinators-dataset/dataset")
BATCH_SIZE = 1000


def validate(dataset: Path, tmp_dir: Path) -> List[Tuple[str, str]]:
    return []


if __name__ == "__main__":

    for partition in ["train", "validation", "test"]:
        logging.info(f"Starting validation of {partition} set...")

        dataset_path = DATASET_DIR
