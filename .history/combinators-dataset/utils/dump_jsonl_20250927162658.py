from pathlib import Path
from typing import List, Tuple
import json
import logging

logging.getLogger(__name__)


def dump_jsonl(path: Path, pairs: List[Tuple[str, str]]):
    try:
        with open(path, "w", encoding="utf-8") as f:
            for type, term in pairs:
                data = {"term": term, "type": type}
                f.write(json.dumps(data) + "\n")
    except Exception as e:
        logging.error(
            f"The following error occurred while dumping the dataset to '{path}' 🛑\n---\n{e}\n---"
        )
        raise e
