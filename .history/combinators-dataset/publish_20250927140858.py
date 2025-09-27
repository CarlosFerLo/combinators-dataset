from datasets import load_dataset
from pathlib import Path

DATASET_DIR = Path("combinators-dataset/dataset")
HUGGINGFACE_DATASET_NAME = "carlosFerLo/combinators-dataset"

if __name__ == "__main__":
    dataset_dict = load_dataset(
        "json",
        data_files={
            "train": str(DATASET_DIR / "train.jsonl"),
            "validation": str(DATASET_DIR / "validation.jsonl"),
            "test": str(DATASET_DIR / "test.jsonl"),
        },
    )

    dataset_dict.push_to_hub(HUGGINGFACE_DATASET_NAME)
