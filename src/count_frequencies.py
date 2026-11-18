from collections import Counter
from pathlib import Path
from itertools import combinations
from mobile_rules import parse_skills, is_mobile
from checkpoint import save_state, load_state, find_latest_checkpoint
import csv
import time

DATASET_PATH = Path(__file__).resolve().parent.parent.parent / "hw_3/it_vacancies_2024.csv"
CHUNK_SIZE = 5000 # как в дз 3

def iter_chunks(reader, chunk_size):
    chunk, i = [], 0
    for row in reader:
        if i >= chunk_size:
            yield chunk
            chunk, i = [], 0
        chunk.append(row)
        i += 1
    if chunk: yield chunk

def map_chunk(chunk):
    skills_single = Counter()
    skills_pairs = Counter()
    skills_triple = Counter()

    for row in chunk:
        if is_mobile(row):
            row_skills = sorted(parse_skills(row))

            skills_single.update(row_skills)
            skills_pairs.update(combinations(row_skills, 2))
            skills_triple.update(combinations(row_skills, 3))

    return skills_single, skills_pairs, skills_triple

def count_frequencies(coord_name, logger, delay, experiment_name, checkpoint_name):
    latest_checkpoint = find_latest_checkpoint(experiment_name)
    if latest_checkpoint is None:
        chunk_num, single, pairs, triple = -1, Counter(), Counter(), Counter()
    else:
        chunk_num, single, pairs, triple = load_state(latest_checkpoint)
        logger.info("%s: Восстановил %s, последний чанк %s",
                coord_name, latest_checkpoint, chunk_num)

    with DATASET_PATH.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, strict=True)

        for i, chunk in enumerate(iter_chunks(reader, CHUNK_SIZE)):
            if i <= chunk_num:
                continue

            counters = map_chunk(chunk)

            single.update(counters[0])
            pairs.update(counters[1])
            triple.update(counters[2])

            save_state(i, single, pairs, triple, experiment_name, f"checkpoint-{checkpoint_name}")
            logger.info("%s: Сохранил чанк %s", coord_name, i)
            time.sleep(delay)

    logger.info(
        "%s: Готово. навыков: %s, пар навыков: %s, троек навыков: %s", 
        coord_name, len(single), len(pairs), len(triple)
    )

    return len(single), len(pairs), len(triple)