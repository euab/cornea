import logging
import asyncio
from typing import Dict, Any, Optional
import argparse

from cornea import database
from cornea.model import Model
from cornea.constants import CONFIG_LOCATION
from cornea.config import load_config_file, Config
from cornea.training import ingest_training_data, load_training_folder

logger = logging.getLogger(__name__)


def create_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cornea",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=""
    )
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--train", action="store_true")
    parser.add_argument('--ingest', action="store", nargs='+', type=str)
    parser.add_argument('--tag', action="store", nargs="+", type=int)

    return parser


def run() -> None:
    parser = create_argument_parser()
    cmdline_arguments = parser.parse_args()

    setup_logging(True)

    config = load_config_file(CONFIG_LOCATION)
    config = Config(config)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    if cmdline_arguments.run:
        serve_application(config, loop)
    elif cmdline_arguments.train:
        loop.run_until_complete(start_and_train_only(config))
    elif cmdline_arguments.ingest:
        loop.run_until_complete(ingest_only(
            config,
            cmdline_arguments.ingest[0],
            cmdline_arguments.tag[0])
        )
    else:
        logger.error("No command specified.")


def setup_logging(debug: bool) -> None:
    level = logging.INFO
    if debug:
        level = logging.DEBUG
    logging.basicConfig(level=level)


async def database_connect(db_config: Dict[str, Any]) -> database.Connection:
    db_config = db_config["postgres"]
    return await database.connect(
        db_config["user"],
        db_config["password"],
        db_config["database"],
        db_config["host"],
        db_config["port"],
        asyncio.get_running_loop()
    )


def serve_application(config: Config, loop: asyncio.AbstractEventLoop) -> None:
    from cornea import server

    app = server.create_server(Model("data/new_model.yml", config), config)
    server_coro = app.create_server(
        return_asyncio_server=True
    )

    logger.info(f"Starting Cornea server on http://127.0.0.1:8000")
    app.ctx.conn = loop.run_until_complete(
        database_connect(config.database)
    )

    task = asyncio.ensure_future(server_coro, loop=loop)
    srv = loop.run_until_complete(task)

    loop.run_until_complete(srv.startup())
    loop.run_until_complete(srv.after_start())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        srv.close()
        loop.close()


async def start_and_train_only(
        config: Config,
    ) -> None:
    model = Model.load_model(None, config, False)
    
    conn = await database_connect(config.database)
    training_data = await database.all_faces(conn)
    model.train(training_data)


async def ingest_only(
        config: Config,
        ingest_folder: str,
        tag: Optional[int]
) -> None:
    if tag is None:
        raise ValueError("Must provide a tag for training folder.")
    conn = await database_connect(config.database)
    td = load_training_folder(ingest_folder, tag)
    await ingest_training_data(conn, td)


if __name__ == '__main__':
    run()
