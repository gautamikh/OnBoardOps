import os
from contextlib import contextmanager

import psycopg
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg.rows import dict_row


@contextmanager
def get_checkpointer():
    with psycopg.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        connect_timeout=3,
        autocommit=True,
        row_factory=dict_row,
        prepare_threshold=0,
    ) as connection:
        yield PostgresSaver(connection)


def setup_checkpoints():
    with get_checkpointer() as checkpointer:
        checkpointer.setup()


if __name__ == "__main__":
    setup_checkpoints()
    print("LangGraph checkpoint storage is ready.")