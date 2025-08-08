from pathlib import Path
from datasets import load_dataset

PATH = Path("combinators-dataset")

if __name__ == "__main__" :
    dataset = load_dataset("json", data_files=str(PATH / "dataset.jsonl"), split="train")
    
    train_valtest = dataset.train_test_split(test_size=0.2, seed=42)
    train_dataset = train_valtest['train']
    valtest_dataset = train_valtest['test']
    
    val_test_split = valtest_dataset.train_test_split(test_size=0.5, seed=42)
    val_dataset = val_test_split['train']
    test_dataset = val_test_split['test']
    
    train_dataset.to_json(PATH / "train.jsonl")
    val_dataset.to_json(PATH / "validation.jsonl")
    test_dataset.to_json(PATH / "test.jsonl")