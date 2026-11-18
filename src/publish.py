import json
import os
from kazoo.exceptions import NodeExistsError, BadVersionError

# FENCING = os.getenv("FENCING") == "1"

def epoch_number(epoch: str) -> int:
    return int(epoch.rsplit("-", 1)[-1])

def publish_result(zk, coord_name, experiment_name, epoch, counts, log):
    zk.ensure_path("/hw4/results")
    path = f"/hw4/results/{experiment_name}"

    try:
        zk.create(path, b"{}")
    except NodeExistsError:
        pass  # сохраняем существующие данные и версию

    result = {
        "coord_name": coord_name,
        "epoch": epoch,
        "single": counts[0],
        "pairs": counts[1],
        "triples": counts[2],
    }
    payload = json.dumps(result, ensure_ascii=False).encode("utf-8")

    if os.getenv("FENCING") != "1":
        stat = zk.set(path, payload)
        log.info("%s: Записал результат, epoch=%s, version=%s", coord_name, epoch, stat.version)
        return True

    for _ in range(5):
        data, current_stat = zk.get(path)
        current = json.loads(data.decode("utf-8"))

        current_epoch = current.get("epoch")
        if current_epoch is not None and epoch_number(current_epoch) > epoch_number(epoch):
            log.error("%s: BadVersionError: устаревшая epoch=%s, текущая epoch=%s", coord_name, epoch, current_epoch)
            return False

        try:
            stat = zk.set(path, payload, version=current_stat.version)
        except BadVersionError:
            continue # указатель изменился после get(); читаем его заново.

        log.info("%s: Записал результат, epoch=%s, version=%s", coord_name, epoch, stat.version)
        return True

    raise RuntimeError("Не удалось опубликовать результат: указатель часто изменяется")