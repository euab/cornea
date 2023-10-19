import os
import logging
from typing import Optional, List, Tuple

import asyncpg
from asyncpg import Connection
from asyncpg.exceptions import PostgresError

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    pass


class Person:
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
                  port: Optional[int]) -> Optional[Connection]:
    
    try:
        logger.info("Connecting to PostgreSQL database: "
                    f"postgres://{username}@{host}:{port}/{database}")
        conn = await asyncpg.connect(
            user=username,
            password=password,
            database=database,
            host=host,
            port=port
        )
    except PostgresError as e:
        msg = (
            f"An error has occured when connecting to database: {database} "
            f"as {username} located at {host}:{port}. Please ensure that the "
            f"database exists.\n\n{e}"
        )
        logger.error(msg)
        return None
    
    logger.info('Connection successful')
    return conn


async def create_tables(conn: Connection) -> bool:
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
    except PostgresError:
        logger.error("Could not create database tables.")
        return False
    
    return True


async def write_person(conn: Connection,
                     first_name: str,
                     last_name: str) -> None:
    sql = """
        INSERT INTO person(first_name, last_name)
        VALUES ($1, $2)
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


async def get_person_by_tag(conn: Connection, tag: int) -> Person:
    sql = "SELECT * from person WHERE id=$1"

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
    sql = """INSERT INTO face(tag, blob) VALUES ($1, $2)"""
    try:
        async with conn.transaction():
            conn.execute(sql, tag, blob)
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


async def all_faces(conn: Connection) -> List[Tuple[int, int, bytes]]:
    query = "SELECT * FROM face"

    try:
        async with conn.transaction():
            rows = conn.fetch(query)
    except PostgresError as e:
        logger.error(f"Error while loading all faces:\n{e}")
        raise DatabaseError
    
    faces = []
    for row in rows:
        face = (row["id"], row["tag"], row["blob"])
        faces.append(face)
    return faces


async def get_faces_by_tag(
        conn: Connection,
        tag: int) -> List[Tuple[int, int, bytes]]:
    query = "SELECT * from face WHERE tag=$1"

    try:
        async with conn.transaction():
            rows = conn.fetch(query, tag)
    except PostgresError as e:
        logger.error(f"Error while fetching faces for tag: {tag}")
        raise DatabaseError
    
    faces = []
    for row in rows:
        face = (row["id", row["tag"], row["blob"]])
        faces.append(face)
    return faces


async def get_face_by_id(
        conn: Connection,
        face_id: int) -> Tuple[int, int, bytes]:
    query = "SELECT * from face where id=$1"

    try:
        async with conn.transaction():
            row = conn.fetchrow(query, face_id)
    except PostgresError as e:
        logger.error(f"Error while fetching face for id: {face_id}")
        raise DatabaseError
    
    return (row["id"], row["tag"], row["blob"])
