import logging
import asyncio

from cornea import database
from cornea.model import Model
from cornea.constants import (
    POSTGRES_DATABASE,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    POSTGRES_HOST,
    POSTGRES_PORT
)

logger = logging.getLogger(__name__)


def run() -> None:
    setup_logging(True)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    #loop.run_until_complete(database.write_person(conn, "John", "Doe"))
    #data = load_training_folder("data/test_dataset", 1)
    #loop.run_until_complete(ingest_training_data(conn, data))
    #train_model(model, data, "data/new_model.yml")
    serve_application(loop)


def setup_logging(debug: bool) -> None:
    level = logging.INFO
    if debug:
        level = logging.DEBUG
    logging.basicConfig(level=level)


def serve_application(loop: asyncio.AbstractEventLoop) -> None:
    from cornea import server

    app = server.create_server(Model("data/new_model.yml"))
    server_coro = app.create_server(
        return_asyncio_server=True
    )

    logger.info(f"Starting Cornea server on http://127.0.0.1:8000")
    app.ctx.conn = loop.run_until_complete(database.connect(
        POSTGRES_USER,
        POSTGRES_PASSWORD,
        POSTGRES_DATABASE,
        POSTGRES_HOST,
        POSTGRES_PORT,
        loop)
    )

    task = asyncio.ensure_future(server_coro, loop=loop)
    srv = loop.run_until_complete(task)

    loop.run_until_complete(srv.startup())
    loop.run_until_complete(srv.after_start())

    loop.run_forever()


if __name__ == '__main__':
    run()
