from datasets import load_dataset
from pathlib import Path

PATH = Path("combinators-dataset")

if __name__ == "__main__" :
    dataset_dict = load_dataset(
        "json", 
        data_files={
            "train": str(PATH / "train.jsonl"),
            "validation": str(PATH / "validation.jsonl"),
            "test": str(PATH / "test.jsonl")
        }
    )
    
    dataset_dict.push_to_hub("carlosFerLo/combinators-dataset")