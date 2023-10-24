import logging
import asyncio
from typing import Dict, Any
import argparse

from cornea import database
from cornea.model import Model
from cornea.constants import CONFIG_LOCATION
from cornea.config import load_config_file

logger = logging.getLogger(__name__)


def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="Cornea",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=""
    )
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--train", action="store_true")

    return parser


def run() -> None:
    parser = create_argument_parser()
    cmdline_arguments = parser.parse_args()

    setup_logging(True)

    config = load_config_file(CONFIG_LOCATION)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    if cmdline_arguments.run:
        serve_application(config, loop)
    elif cmdline_arguments.train:
        loop.run_until_complete(start_and_train_only(config))
    else:
        logger.error("No command specified.")


def setup_logging(debug: bool) -> None:
    level = logging.INFO
    if debug:
        level = logging.DEBUG
    logging.basicConfig(level=level)


async def database_connect(db_config: Dict[Any, Any]) -> database.Connection:
    return await database.connect(
        db_config["user"],
        db_config["password"],
        db_config["database"],
        db_config["host"],
        db_config["port"],
        asyncio.get_running_loop()
    )


def serve_application(config: Dict[Any, Any], loop: asyncio.AbstractEventLoop) -> None:
    from cornea import server

    app = server.create_server(Model("data/new_model.yml", config), config)
    server_coro = app.create_server(
        return_asyncio_server=True
    )

    logger.info(f"Starting Cornea server on http://127.0.0.1:8000")
    app.ctx.conn = loop.run_until_complete(
        database_connect(config["postgres"])
    )

    task = asyncio.ensure_future(server_coro, loop=loop)
    srv = loop.run_until_complete(task)

    loop.run_until_complete(srv.startup())
    loop.run_until_complete(srv.after_start())

    loop.run_forever()


async def start_and_train_only(
        config: Dict[Any, Any],
    ) -> None:
    model = Model.load_model(config["model_default_path"], config=config)
    
    conn = await database_connect(config["postgres"])
    training_data = await database.all_faces(conn)
    model.train(training_data)


if __name__ == '__main__':
    run()
