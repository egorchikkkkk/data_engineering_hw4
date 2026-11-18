# ДЗ 4. Обеспечение отказоустойчивости средствами Apache ZooKeeper

## Описание

Проект продолжает расчёт частот навыков, пар и троек из ДЗ 3. Ансамбль из трёх серверов ZooKeeper выбирает лидера среди двух координаторов. После каждого обработанного чанка лидер сохраняет чекпоинт; запасной координатор при смене лидера продолжает расчёт с него. Публикацию результата можно запустить без защиты или с проверкой эпохи (`FENCING=1`).

## Запуск

Понадобятся Docker с Docker Compose, `uv` и Python 3.13. Исходный файл `hw_3/it_vacancies_2024.csv` должен лежать рядом с каталогом `hw_4`: путь к нему задан в `src/count_frequencies.py`.

1. Из каталога `hw_4` запустить ансамбль и установить зависимости:

    ```bash
    docker compose up -d
    uv sync --locked
    ```

2. Проверить роли серверов (один `leader`, два `follower`):

    ```bash
    docker compose exec zk1 zkServer.sh status
    docker compose exec zk2 zkServer.sh status
    docker compose exec zk3 zkServer.sh status
    ```

3. Для обычного запуска открыть два терминала в каталоге `hw_4`. Запустить A, затем B с одинаковым **новым** именем эксперимента:

    ```bash
    uv run --locked python src/election.py --name A --delay 1 --experiment-name trial-01 2>&1 | tee logs/trial_A.log
    ```

    ```bash
    uv run --locked python src/election.py --name B --delay 1 --experiment-name trial-01 2>&1 | tee logs/trial_B.log
    ```

    Координаторы остаются подключёнными после окончания расчёта. Завершить их можно через `Ctrl+C`. Для нового опыта используйте другое имя: чекпоинты и указатель результата сохраняются между запусками.

4. Для опыта с защитой запускать **оба** координатора с `FENCING=1` и ещё одним новым именем эксперимента:

    ```bash
    FENCING=1 uv run --locked python src/election.py --name A --delay 1 --experiment-name fencing-trial-01 2>&1 | tee logs/fencing_trial_A.log
    ```

    ```bash
    FENCING=1 uv run --locked python src/election.py --name B --delay 1 --experiment-name fencing-trial-01 2>&1 | tee logs/fencing_trial_B.log
    ```

    Чтобы воспроизвести отказ, найдите PID именно Python-процесса лидера командой `ps -axo pid,comm,args | grep '[e]lection.py'` и приостановите его через `kill -STOP <PID>`. После публикации результата запасным координатором возобновите старый процесс через `kill -CONT <PID>`. Не останавливайте серверы ZooKeeper во время этого опыта.

5. Прочитать опубликованный результат и версию указателя:

    ```bash
    docker compose exec -T zk1 zkCli.sh -server zk1:2181 get -s /hw4/results/trial-01
    ```

    Подставьте имя своего эксперимента. Для остановки ансамбля используйте `docker compose stop`; тома с данными при этом сохранятся.

## Структура проекта

| Файл или каталог | Назначение |
|---|---|
| `compose.yaml` | Три сервера ZooKeeper 3.9.6 с раздельными томами и портами |
| `src/election.py` | Подключение к ZooKeeper, выбор лидера и запуск расчёта |
| `src/count_frequencies.py` | Чтение CSV и подсчёт частот по чанкам |
| `src/checkpoint.py` | Сохранение и поиск чекпоинта по эпохе |
| `src/publish.py` | Публикация указателя на результат, в том числе с `FENCING=1` |
| `src/mobile_rules.py` | Правила отбора вакансий и нормализации навыков из ДЗ 3 |
| `logs/` | Журналы координаторов и время приостановки лидера |
| `state/` | Локальные бинарные чекпоинты; не включаются в Git |
| `pyproject.toml`, `uv.lock` | Зависимости и их зафиксированные версии |

## Материалы запусков

- Без защиты:
    - [координатор A](logs/no_fencing_A.log)
    - [координатор B](logs/no_fencing_B.log)
    - [время паузы](logs/no_fencing_pause.txt)

- С защитой:
    - [координатор A](logs/fencing_A.log)
    - [координатор B](logs/fencing_B.log)
    - [время паузы](logs/fencing_pause.txt)

- [Проверка восстановления с чекпоинта](logs/checkpoint_B.log)