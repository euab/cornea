import logging

from cornea import server

logger = logging.getLogger(__name__)


def run() -> None:
    setup_logging(True)
    serve_application()


def setup_logging(debug: bool) -> None:
    level = logging.INFO
    if debug:
        level = logging.DEBUG
    logging.basicConfig(level=level)


def serve_application() -> None:
    app = server.create_server()
    logger.info(f"Starting Cornea server on http://127.0.0.1:8000")
    app.run(host="0.0.0.0", port=8000)


if __name__ == '__main__':
    run()
