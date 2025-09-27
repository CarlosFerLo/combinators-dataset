from typing import Dict, List, Tuple, Set, Optional
import json
from pathlib import Path
import logging
import sqlite3
import sys
import multiprocessing as mp
from multiprocessing.managers import BaseManager
import time
import random
import os
import threading
from .annotation import annotate, parse_sk


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(threadName)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

DATASET_PATH = Path("combinators-dataset/dataset")
SEEN_DB_PATH = Path("combinators-dataset/seen")

BATCH_SIZE = 1000

MAX_DEPTH = 6


class Error(Exception):
    def __init__(self, original_exception: Exception):
        super().__init__(str(original_exception))
        self.original_exception = original_exception


class MyManager(BaseManager):
    pass


class CombinatorsDataset:
    _typed_pairs: Dict[str, List[str]] = {}

    def __init__(self) -> None:

        self._typed_pairs = {}

    def __getitem__(self, key: str) -> List[str]:
        return self._typed_pairs.get(key, [])

    def __setitem__(self, key: str, value: List[str]) -> None:
        self._typed_pairs[key] = value

    def __len__(self) -> int:
        return sum(len(self[t]) for t in self._typed_pairs)

    def length(self) -> int:
        return len(self)

    def add(self, type: str, term: str) -> bool:
        terms = self[type] + [term]
        ordered_terms = sorted(terms, key=lambda x: len(x))
        self[type] = ordered_terms[:5]
        return term in self[type]

    def extend(self, pairs: List[Tuple[str, str]]) -> int:
        new = 0
        for pair in pairs:
            if self.add(type=pair[0], term=pair[1]):
                new += 1
        return new

    def get_partitions(
        self, val: float = 0.1, test: float = 0.1
    ) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]], List[Tuple[str, str]]]:

        test = 1 - val - test
        if test < 0:
            raise ValueError("Partitions must add up to 1")

        types = list(self._typed_pairs.keys())

        random.shuffle(types)

        n = len(types)
        cut1 = int(n * train)
        cut2 = cut1 + int(n * val)

        train_types = types[:cut1]
        val_types = types[cut1:cut2]
        test_types = types[cut2:]

        def get_pairs(types: List[str]) -> List[Tuple[str, str]]:
            pairs: List[Tuple[str, str]] = []
            for type in types:
                pairs.extend([(type, term) for term in self[type]])
            return pairs

        train_pairs = get_pairs(train_types)
        val_pairs = get_pairs(val_types)
        test_pairs = get_pairs(test_types)

        return train_pairs, val_pairs, test_pairs

    @staticmethod
    def to_jsonl(path: Path, pairs: List[Tuple[str, str]]):
        try:
            with open(path, "w", encoding="utf-8") as f:
                for type, term in pairs:
                    data = {"term": term, "type": type}
                    f.write(json.dumps(data) + "\n")
        except Exception as e:
            logging.error(
                f"The following error occurred while dumping the dataset to '{path}' 🛑\n---\n{e}\n---"
            )
            raise Error(e) from e


MyManager.register("CombinatorsDataset", CombinatorsDataset)


class SeenDB:
    """A tiny wrapper around sqlite for persistent 'seen' set of SK strings."""

    def __init__(self, path: Path):
        try:
            self.path = path
            self.conn = sqlite3.connect(str(path), check_same_thread=False)
            self.conn.execute("PRAGMA journal_mode=WAL;")
            self.conn.execute("CREATE TABLE IF NOT EXISTS seen (term TEXT PRIMARY KEY)")
            self.conn.commit()
            logging.info("SeenDB initialized correctly ✅")
        except Exception as e:
            logging.error(
                "The following error occurred while initializing SeenDB 🛑\n---\n{e}\n---"
            )
            raise Error(e) from e

    def add_if_new(self, term: str) -> bool:
        """Return True if term was new (and is now inserted), False if already seen."""
        try:
            self.conn.execute("INSERT INTO seen (term) VALUES (?)", (term,))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def close(self) -> None:
        self.conn.close()
        logging.info("Closing SeenDB connection")


def sk_generation_process(q_gen) -> None:
    counter = 0
    while True:

        def generate_combinator(max_depth: int = 6) -> str:
            if max_depth == 0:
                return random.choice(["S", "K"])
            else:
                choice = random.random()
                if choice < 0.3:
                    return random.choice(["S", "K"])
                else:
                    left = generate_combinator(max_depth - 1)
                    right = generate_combinator(max_depth - 1)
                    return f"({left} {right})"

        expr = generate_combinator(MAX_DEPTH)
        q_gen.put(expr)
        logging.debug(f"[Gen {os.getpid()}] Generated string: {expr}")
        counter += 1

        if counter % 10_000 == 0:
            logging.info(f"[Gen {os.getpid()}] Total strings generated: {counter}")


def dedup_and_batching_process(q_in, q_out) -> None:
    batch = []
    seen = SeenDB(SEEN_DB_PATH)
    while True:
        term = q_in.get()

        if term == "STOP":
            logging.info(f"[Dedup {os.getpid()}]Stopping gracefully...")
            q_out.put(batch)
            break

        if seen.add_if_new(term):
            batch.append(term)
            logging.debug(f"[Dedup {os.getpid()}] Accepted string: {term}")
        else:
            logging.debug(f"[Dedup {os.getpid()}] Dropped duplicate: {term}")

        if len(batch) >= BATCH_SIZE:
            q_out.put(batch)
            batch = []
            logging.info(f"[Dedup {os.getpid()}] Passed new batch")


def type_annotation_process(q_in, dataset: CombinatorsDataset) -> None:
    while True:
        try:
            batch = q_in.get(timeout=1.0)
        except Exception:
            continue
        if isinstance(batch, str) and batch == "STOP":
            logging.info(f"[Proc {os.getpid()}]Stopping gracefully...")
            break
        # Run Lean on the batch
        if isinstance(batch, list):
            parsed_pairs = [(expr, parse_sk(expr)) for expr in batch]
            results: List[Tuple[str, str]] = []

            for term, tree in parsed_pairs:
                try:
                    results.append((annotate(tree)["type"], term))
                except Exception:
                    continue

            if results:
                new = dataset.extend(results)
                logging.info(
                    f"[Proc {os.getpid()}] Found {len(results)} valid pairs, {new} were new (total: {dataset.length()})"
                )


def monitor_processes(processes, interval=5):
    while True:
        all_alive = True
        for p in processes:
            if not p.is_alive():
                logging.warning(f"[Monitor] Process {p.name} is NOT alive!")
                all_alive = False
        if not all_alive:
            logging.warning(
                "[Monitor] One or more processes are dead. Stopping monitor."
            )
            break
        else:
            logging.info("[Monitor] All processes are alive.")
        time.sleep(interval)


if __name__ == "__main__":

    logging.info("Initializing data sources...")

    manager = MyManager()
    manager.start()

    try:
        if not DATASET_PATH.exists():
            logging.info(f"Creating {DATASET_PATH} folder")
            DATASET_PATH.mkdir()
        dataset = manager.CombinatorsDataset()  # type: ignore
    except Error:
        logging.info("Exiting...")
        sys.exit()

    logging.info("Initializing workers...")

    q_gen_dedup = mp.Queue(maxsize=100)
    q_dedup_proc = mp.Queue(maxsize=100)

    p1 = mp.Process(target=sk_generation_process, args=(q_gen_dedup,))
    p2 = mp.Process(target=dedup_and_batching_process, args=(q_gen_dedup, q_dedup_proc))
    p3 = mp.Process(target=type_annotation_process, args=(q_dedup_proc, dataset))

    logging.info("Starting processes...")
    p1.start()
    p2.start()
    p3.start()

    processes = [p1, p2, p3]

    # Start monitor in a separate thread
    monitor_thread = threading.Thread(target=monitor_processes, args=(processes,))
    monitor_thread.daemon = True
    monitor_thread.start()

    try:
        p1.join()
        p2.join()
        p3.join()

    except KeyboardInterrupt:
        logging.info("Stopping processes...")
        p1.terminate()

    finally:

        logging.info("Terminating Dedup...")

        q_gen_dedup.put("STOP")

        p2.join()

        logging.info("Terminating Annotator...")

        q_dedup_proc.put("STOP")

        p3.join()

        train, val, test = dataset.get_partitions()

        logging.info(
            f"Dumping test set to {DATASET_PATH / 'train.jsonl'}... (length: {len(train)})"
        )
        CombinatorsDataset.to_jsonl(DATASET_PATH / "train.jsonl", train)

        logging.info(
            f"Dumping validation set to {DATASET_PATH / 'validation.jsonl'}... (length: {len(val)})"
        )
        CombinatorsDataset.to_jsonl(DATASET_PATH / "validation.jsonl", val)

        logging.info(
            f"Dumping test set to {DATASET_PATH / 'test.jsonl'}... (length: {len(test)})"
        )
        CombinatorsDataset.to_jsonl(DATASET_PATH / "test.jsonl", test)

        manager.shutdown()

        logging.info("Stopped gracefully")
