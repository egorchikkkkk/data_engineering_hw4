import argparse
import logging
from threading import Event
from kazoo.client import KazooClient
from kazoo.protocol.states import KazooState
from count_frequencies import count_frequencies
from publish import publish_result

ELECTION_PATH = "/hw4/election"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True)
    parser.add_argument("--delay", type=float, default=0.2)
    parser.add_argument("--experiment-name", required=True)
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    log = logging.getLogger(args.name)

    wake = Event()
    session_lost = Event()

    zk = KazooClient(
        hosts='127.0.0.1:2181,127.0.0.1:2182,127.0.0.1:2183',
        timeout=10
    )

    def on_state(state):
        log.info("Состояние соединения: %s", state)

        if state == KazooState.LOST:
            session_lost.set()

        wake.set()

    def on_predecessor_change(event):
        log.info("Изменился предшественник: %s", event)
        wake.set()

    zk.add_listener(on_state)
    zk.start(timeout=15)
    zk.ensure_path(ELECTION_PATH)

    candidate_name = None
    is_leader = False

    try:
        while True:
            if session_lost.is_set():
                candidate_name = None
                is_leader = False
                session_lost.clear()

            if zk.state != KazooState.CONNECTED:
                wake.clear()

                # проверяем повторно, состояние могло измениться после очистки события
                if zk.state != KazooState.CONNECTED:
                    wake.wait(timeout=1)

                continue

            if candidate_name is None:
                path = zk.create(
                    f"{ELECTION_PATH}/candidate-",
                    ephemeral=True,
                    sequence=True,
                )
                candidate_name = path.rsplit("/", 1)[-1]
                log.info("Создал узел %s", path)

            children = sorted(zk.get_children(ELECTION_PATH))
            position = children.index(candidate_name)

            if position == 0:
                if not is_leader:
                    is_leader = True
                    log.info("Стал лидером: %s", candidate_name)
                    counts = count_frequencies(args.name, log, args.delay, args.experiment_name, candidate_name)
                    publish_result(zk, args.name, args.experiment_name, candidate_name, counts, log)
                if session_lost.is_set():
                    continue
                wake.clear()
                if zk.state == KazooState.CONNECTED:
                    wake.wait()
                continue

            is_leader = False
            predecessor = children[position-1]
            predecessor_path = f"{ELECTION_PATH}/{predecessor}"
            log.info("Ожидаю предшественника %s", predecessor)

            wake.clear()
            stat = zk.exists(predecessor_path, watch=on_predecessor_change)

            if stat is None:
                continue

            wake.wait()

    except KeyboardInterrupt:
        log.info("Завершение работы")
    finally:
        zk.stop()
        zk.close()

if __name__ == "__main__":
    main()