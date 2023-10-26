import os
import logging
import asyncio
from typing import Optional, List, Tuple

import asyncpg
from asyncpg import Connection
from asyncpg.exceptions import PostgresError

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Exception class for generic database errors."""
    pass


class Person:
    """Representation of a person in the person table"""
    def __init__(self,
                 tag: int,
                 first_name: str,
                 last_name: str
    ) -> None:
        self.tag = tag
        self.first_name = first_name
        self.last_name = last_name


async def connect(username: Optional[str],
                  password: Optional[str],
                  database: Optional[str],
                  host: Optional[str],
                  port: Optional[int],
                  loop: asyncio.AbstractEventLoop
                  ) -> Optional[Connection]:
    """
    Attempt to establish a connection to the PostgreSQL database.
    On connecting to the database, this code will check if all
    database relations have been set up and will set them up if they have not.
    """
    try:
        logger.info("Connecting to PostgreSQL database: "
                    f"postgres://{username}@{host}:{port}/{database}")
        conn = await asyncpg.connect(
            user=username,
            password=password,
            database=database,
            host=host,
            port=port,
            loop=loop
        )
    except PostgresError as e:
        msg = (
            f"An error has occured when connecting to database: {database} "
            f"as {username} located at {host}:{port}. Please ensure that the "
            f"database exists.\n\n{e}"
        )
        logger.error(msg)
        return None
    
    if not await create_tables(conn):
        return None

    logger.info('Connection successful')
    return conn


async def create_tables(conn: Connection) -> bool:
    """Create tables in the database needed to run Cornea."""
    logger.info("Creating database tables")
    sql = """
        CREATE TABLE IF NOT EXISTS person(
            id SERIAL PRIMARY KEY,
            first_name TEXT,
            last_name TEXT
        );
        CREATE TABLE IF NOT EXISTS face(
            id SERIAL PRIMARY KEY,
            tag INTEGER REFERENCES person(id),
            face_data BYTEA
        );
    """

    try:
        async with conn.transaction():
            await conn.execute(sql)
    except PostgresError as e:
        logger.error(f"Could not create database tables.\n{e}")
        return False
    
    return True


async def write_person(conn: Connection,
                     first_name: str,
                     last_name: str) -> None:
    """Write a new person to the database"""
    sql = """
        INSERT INTO person (first_name, last_name)
        VALUES ($1, $2);
    """
    try:
        async with conn.transaction():
            await conn.execute(sql, first_name, last_name)
    except PostgresError as e:
        logger.error(
            f'Could not add face {first_name} {last_name} to the database.\n'
            f'Error: {e}'
        )
        return


def get_person_by_tag_sync(conn: Connection, tag: int) -> Optional[Person]:
    """Synchronous option to fetch a person from the database."""
    return asyncio.run(get_faces_by_tag, conn, tag)


async def get_person_by_tag(conn: Connection, tag: int) -> Optional[Person]:
    """Get a person by their training tag from the database."""
    sql = "SELECT * from person WHERE id=$1;"

    try:
        async with conn.transaction():
            row = await conn.fetchrow(sql, tag)
    except PostgresError as e:
        logger.error(f"Could not retreive tag: {tag} from database.\n"
                     f"Error: {e}"
        )
        return None
    
    person = Person(
        tag=row["id"],
        first_name=row["first_name"],
        last_name=row["last_name"]
    )

    return person


async def _write_face(
    conn: Connection,
    tag: int,
    blob: bytes
) -> bool:
    """Write a face sample to the database"""
    sql = """INSERT INTO face (tag, face_data) VALUES ($1, $2);"""
    try:
        async with conn.transaction():
            await conn.execute(sql, tag, blob)
    except PostgresError as e:
        logger.error(e)
        return False
    return True


async def write_face_data_from_image(
        conn: Connection,
        tag: int,
        fp: str) -> None:
    if not os.path.exists((path := os.path.abspath(fp))):
        return False
    
    with open(path, 'rb') as image:
        image_data = image.read()
    
    if not await _write_face(conn, tag, image_data):
        raise DatabaseError(
            f"Could not write face beloging to tag: {tag} to the database."
        )


async def all_faces(conn: Connection) -> List[Tuple[bytes, int]]:
    """Get all faces and their training tags from the database."""
    query = "SELECT * FROM face;"

    try:
        async with conn.transaction():
            rows = await conn.fetch(query)
    except PostgresError as e:
        logger.error(f"Error while loading all faces:\n{e}")
        raise DatabaseError
    
    faces = []
    for row in rows:
        face = (row["face_data"], row["tag"])
        faces.append(face)
    return faces


async def get_faces_by_tag(
        conn: Connection,
        tag: int) -> List[Tuple[int, int, bytes]]:
    """Get a group of faces by their training tag"""
    query = "SELECT * from face WHERE tag=$1;"

    try:
        async with conn.transaction():
            rows = await conn.fetch(query, tag)
    except PostgresError as e:
        logger.error(f"Error while fetching faces for tag: {tag}")
        raise DatabaseError
    
    faces = []
    for row in rows:
        face = (row["id", row["tag"], row["face_data"]])
        faces.append(face)
    return faces


async def get_face_by_id(
        conn: Connection,
        face_id: int) -> Tuple[int, int, bytes]:
    """Get a face by its database primary key"""
    query = "SELECT * from face WHERE id=$1;"

    try:
        async with conn.transaction():
            row = await conn.fetchrow(query, face_id)
    except PostgresError as e:
        logger.error(f"Error while fetching face for id: {face_id}")
        raise DatabaseError
    
    return (row["id"], row["tag"], row["face_data"])
