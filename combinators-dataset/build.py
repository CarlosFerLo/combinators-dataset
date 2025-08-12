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
import re
import tempfile
import subprocess
import threading

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(threadName)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S"
)

DATASET_PATH = Path("combinators-dataset/dataset.jsonl")
SEEN_DB_PATH = Path("combinators-dataset/seen")

BATCH_SIZE = 1000
MAX_BACKLOG = 1_000_000

MAX_DEPTH = 6

class Error (Exception) :
    def __init__(self, original_exception: Exception):
        super().__init__(str(original_exception))  
        self.original_exception = original_exception
        
class MyManager (BaseManager) :
    pass

class CombinatorsDataset () :
    _typed_pairs : Dict[str, List[str]] = {}
    
    def __init__ (self, path: Optional[Path] = None) -> None :
        
        self._typed_pairs = {}
        
        if path :
            logging.info(f"Loading dataset from '{path}'...")
            try :
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        pair = json.loads(line)
                        self.add(pair["type"], pair["term"])
                    
                logging.info(f"Finished loading the dataset (entries: {len(self)}) ✅")
                
                    
            except Exception as e :
                logging.error(f"The following error occurred while retrieving the dataset from '{path}' 🛑\n---\n{e}\n---")
                raise Error(e) from e
    
    def __getitem__(self, key: str) -> List[str] :
        return self._typed_pairs.get(key, [])
        
    def __setitem__(self, key: str, value: List[str]) -> None :
        self._typed_pairs[key] = value
        
    def __len__ (self) -> int :
        return sum(len(self[t]) for t in self._typed_pairs)
        
    def length (self) -> int :
        return len(self)
        
    def add (self, type: str, term: str) -> None :
        terms = self[type] + [term]
        ordered_terms = sorted(terms, key=lambda x: len(x))
        self[type] = ordered_terms[:5]
        
    def extend (self, pairs: List[Tuple[str, str]]) :
        for pair in pairs :
            self.add(type=pair[0], term=pair[1])
        
    def to_jsonl (self, path: Path) :
        logging.info(f"Dumping dataset to file: '{path}'...")
        try :
            with open(path, "w", encoding="utf-8") as f :
                for type in self._typed_pairs :
                    for term in self[type] :
                        data = {
                            "term": term,  
                            "type": type 
                        }
                        f.write(json.dumps(data) + '\n')
        except Exception as e :
            logging.error(f"The following error occurred while dumping the dataset to '{path}' 🛑\n---\n{e}\n---")
            raise Error(e) from e

MyManager.register("CombinatorsDataset", CombinatorsDataset)
            
class SeenDB:
    """A tiny wrapper around sqlite for persistent 'seen' set of SK strings."""

    def __init__(self, path: Path):
        try :
            self.path = path
            self.conn = sqlite3.connect(str(path), check_same_thread=False)
            self.conn.execute("PRAGMA journal_mode=WAL;")
            self.conn.execute(
                "CREATE TABLE IF NOT EXISTS seen (term TEXT PRIMARY KEY)"
            )
            self.conn.commit()
            logging.info("SeenDB initialized correctly ✅")
        except Exception as e :
            logging.error("The following error occurred while initializing SeenDB 🛑\n---\n{e}\n---")
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
        
def sk_generation_process (q_gen) -> None :
    counter = 0
    while True :
        
        def generate_combinator(max_depth: int=6) -> str:
            if max_depth == 0:
                return random.choice(['S', 'K'])
            else:
                choice = random.random()
                if choice < 0.3:
                    return random.choice(['S', 'K'])
                else:
                    left = generate_combinator(max_depth - 1)
                    right = generate_combinator(max_depth - 1)
                    return f'({left} {right})'
                
        expr = generate_combinator(MAX_DEPTH)
        q_gen.put(expr)  
        logging.debug(f"[Gen {os.getpid()}] Generated string: {expr}")
        counter += 1
        
        if counter % 10_000 == 0 :
            logging.info(f"[Gen {os.getpid()}] Total strings generated: {counter}")
            
def dedup_and_batching_process (q_in, q_out) -> None :
    batch = []
    seen = SeenDB(SEEN_DB_PATH)
    while True :
        term = q_in.get() 
        if seen.add_if_new(term) :
            batch.append(term)
            logging.debug(f"[Dedup {os.getpid()}] Accepted string: {term}")
        else :
            logging.debug(f"[Dedup {os.getpid()}] Dropped duplicate: {term}")
            
        if len(batch) >= BATCH_SIZE :
            q_out.put(batch)
            batch = []
            logging.info(f"[Dedup {os.getpid()}] Passed new batch")
            
def run_lean_batch(sk_terms: List[str], timeout_sec: int = 30) -> List[Tuple[str, str]]:

    # ---------- create temporary file ----------
    with tempfile.NamedTemporaryFile(mode="w", suffix=".lean", delete=False) as tmp:
        tmp_path = tmp.name
        tmp.write("universe u\nvariable {α β γ : Type u}\ndef S (f: α → β → γ) (g: α → β) (x: α) : γ := f x (g x)\ndef K (x: α) (_: β) : α := x\n")
        for term in sk_terms:
            tmp.write(f'#print "[[{term}]]"\n#check {term}')
        tmp.flush()

    # ---------- run lean ----------
    try:
        proc = subprocess.run(["lean", tmp_path], capture_output=True, text=True, timeout=timeout_sec)
        stdout = proc.stdout
        stderr = proc.stderr
    except Exception as e:
        stdout = ""
        stderr = f"Lean run failed: {e}"
        logging.warning("Subprocess error:", stderr)

    # ---------- parse stdout ----------
    valid: List[Tuple[str, str]] = []
    
    if stdout:
                    
        statements : List[str] = re.split(r'\[\[.*?\]\]', stdout)
        statements = list(map(lambda x : x.strip(), statements))

        for statement in statements :
            m = re.match(r'^(?P<term>[SK() ]+?)\s*:\s*(?P<type>.+)$', statement)

            if m is not None :
                valid.append((m.group("term"), m.group("type")))

    # cleanup tmp file
    try:
        os.remove(tmp_path)
    except Exception:
        pass
    
    normalized: List[Tuple[str, str]] = []
    for entry in valid:
        type_str = entry[1]
        matches = list(re.finditer(r"\?m\.\d+", type_str))

        # Deduplicate in order of appearance
        meta_vars: List[str] = []
        seen: Set[str] = set()
        for m in matches:
            mv = m.group()
            if mv not in seen:
                seen.add(mv)
                meta_vars.append(mv)

        if len(meta_vars) > 26:
            # Skip if more than A-Z needed
            continue

        replacement_map = {mv: chr(65 + i) for i, mv in enumerate(meta_vars)}
        new_type = type_str
        for mv, rep in replacement_map.items():
            new_type = new_type.replace(mv, rep)
            
        new_type = new_type.replace("\u2192", "->")
        
        normalized.append((new_type, entry[0]))

    return normalized
            
def lean_batch_process (q_in, dataset: CombinatorsDataset) -> None :
    while True :
        try:
            batch = q_in.get(timeout=1.0)
        except Exception:
            continue
        if isinstance(batch, str) and batch == "STOP":
            break
        # Run Lean on the batch
        if isinstance(batch, list) :
            results = run_lean_batch(batch)
            if results:
                dataset.extend(results)
                logging.info(f"[Proc {os.getpid()}] Found {len(results)} valid pairs (total: {dataset.length()})")

def monitor_processes(processes, interval=5):
    while True:
        all_alive = True
        for p in processes:
            if not p.is_alive():
                logging.warning(f"[Monitor] Process {p.name} is NOT alive!")
                all_alive = False
        if not all_alive:
            logging.warning("[Monitor] One or more processes are dead. Stopping monitor.")
            break
        else :
            logging.info("[Monitor] All processes are alive.")
        time.sleep(interval)
        
if __name__ == "__main__" :
    
    logging.info("Initializing data sources...")
    
    manager = MyManager()
    manager.start()
    
    try :
        if not DATASET_PATH.exists() :
            logging.info(f"Creating {DATASET_PATH} file")
            DATASET_PATH.touch()
        dataset = manager.CombinatorsDataset(DATASET_PATH)
    except Error :
        logging.info("Exiting...")
        sys.exit()
    
    logging.info("Initializing workers...")
    
    q_gen_dedup = mp.Queue(maxsize=1000)
    q_dedup_proc = mp.Queue(maxsize=100)

    p1 = mp.Process(target=sk_generation_process, args=(q_gen_dedup,))
    p2 = mp.Process(target=dedup_and_batching_process, args=(q_gen_dedup, q_dedup_proc))
    p3 = mp.Process(target=lean_batch_process, args=(q_dedup_proc, dataset))
    p4 = mp.Process(target=lean_batch_process, args=(q_dedup_proc, dataset))
    p5 = mp.Process(target=lean_batch_process, args=(q_dedup_proc, dataset))
    
    logging.info("Starting processes...")
    p1.start()
    p2.start()
    p3.start()
    p4.start()
    p5.start()
    
    processes = [p1, p2, p3, p4, p5]
    
    # Start monitor in a separate thread
    monitor_thread = threading.Thread(target=monitor_processes, args=(processes,))
    monitor_thread.daemon = True
    monitor_thread.start()
    
    try :
        p1.join()
        p2.join()
        p3.join()
        p4.join()
        p5.join()
    except KeyboardInterrupt :
        logging.info("Stopping processes...")
        p1.terminate()
        p2.terminate()
        p3.terminate()
        p4.terminate()
        p5.terminate()

        dataset.to_jsonl(DATASET_PATH)
        
        manager.shutdown()
        
        logging.info("Stopped gracefully")
