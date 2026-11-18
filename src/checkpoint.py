import pickle
from collections import Counter
from pathlib import Path
import os

CHECKPOINT_DIR = Path(__file__).resolve().parent.parent / "state"

def find_latest_checkpoint(experiment_name: str):
    experiment_dir = CHECKPOINT_DIR / experiment_name
    files = experiment_dir.glob("checkpoint-candidate-*.pkl")

    latest = max(
        files,
        key=lambda path: int(path.stem.rsplit("-", 1)[-1]),
        default=None,
    )
    if latest is None:
        return None

    return f"{experiment_name}/{latest.stem}"

def save_state(
        chunk_num: int, 
        single: Counter, 
        pairs: Counter, 
        triple: Counter, 
        experiment_name: str, 
        checkpoint_name: str
    ):
    experiment_dir = CHECKPOINT_DIR / experiment_name
    experiment_dir.mkdir(parents=True, exist_ok=True)

    with open(experiment_dir / (checkpoint_name + ".tmp"), "wb") as file:
        pickle.dump((chunk_num, single, pairs, triple), file)

    os.replace(experiment_dir / (checkpoint_name + ".tmp"), experiment_dir / (checkpoint_name + ".pkl"))

def load_state(checkpoint_path: str):
    try:
        with open(CHECKPOINT_DIR / (checkpoint_path + ".pkl"), "rb") as file:
            chunk_num, single, pairs, triple = pickle.load(file)
    except FileNotFoundError:
        return -1, Counter(), Counter(), Counter()

    return chunk_num, single, pairs, triple