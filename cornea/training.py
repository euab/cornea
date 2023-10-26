import os
import logging
from typing import Optional, List, Tuple
from PIL import Image
from io import BytesIO

import numpy as np
from numpy.typing import NDArray

from cornea import database
from cornea.database import Connection
from cornea.model import Model

logger = logging.getLogger(__name__)

ACCEPTED_EXTENSIONS= (".jpg", ".jpeg")


def load_training_file(path: str) -> Optional[bytes]:
    if not os.path.exists(os.path.abspath(path)):
        return
    
    logger.info(f"Loading file at path: {path}")
    try:
        with open(path, 'rb') as image:
            image_data = image.read()
    except OSError:
        return None

    if not image_data:
        return None
    return image_data
    

def load_training_folder(path: str, tag: int) -> List[Tuple[bytes, int]]:
    """
    Ingest a folder of photos into the database.
    Currently, only one known face at a time
    """
    if not os.path.isdir(path) or not os.listdir(path):
        return None
    
    images = []
    files = [image for image in os.listdir(path)]
    for image in files:
        if not image.lower().endswith(ACCEPTED_EXTENSIONS):
            continue

        image_data = load_training_file(f"{path}/{image}")
        if image_data is None:
            logger.warning(f'Unable to load training image for tag: {tag} '
                           f'at path {path}.')
            continue

        entry = (image_data, tag)
        images.append(entry)
    
    return images


async def ingest_training_data(
        conn: Connection,
        data: List[Tuple[bytes, int]]) -> None:
    logger.info("Ingesting training data to database")
    tag = data[0][1]

    actor = await database.get_person_by_tag(conn, 1)
    if actor is None:
        logger.warning(f"No person exists to map to tag: {tag}")
        return

    for entry in data:
        await database._write_face(conn, tag, entry[0])
