# SPDX-License-Identifier gpl2-only
#
# Copyright (C) 2023, Euan Mills. All Rights Reserved.
# This project is licesned under the GPL-2.0 License.
# See the file COPYING for more details.

import base64
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Coroutine
from functools import wraps

from sanic import Sanic, response
from sanic.request import Request
from sanic.response import HTTPResponse, json
from sanic.exceptions import SanicException

from cornea.model import Model
from cornea import database

model: Model = Model("data/new_model.yml")
app = Sanic("cornea_server")

def add_root_route(app: Sanic) -> None:
    @app.get('/')
    async def hello(request: Request) -> HTTPResponse:
        return response.text("Hello from Cornea version: 0.0.0-alpha1")


def threaded_request(func: Callable[..., Coroutine]) -> Callable:
    @wraps(func)
    async def inner(
        request: Request, *args: Any, **kwargs: Any
    ) -> HTTPResponse:
        def run() -> HTTPResponse:
            return asyncio.run(func(request, *args, **kwargs))
        
        with ThreadPoolExecutor() as pool:
            return await request.app.loop.run_in_executor(pool, run)


def create_server(
        model: Model
) -> Sanic:
    app.ctx.model = model
    
    add_root_route(app)

    @app.post('/model/detect_frame')
    async def detect_frame(request: Request) -> HTTPResponse:
        data = request.json
        decoded = base64.b64decode(bytes(data["frame"], encoding='utf8'))
        result = await model.handle_frame(decoded)

        match_data: dict
        if result is None:
            match_data = {
                "tag": "Unknown",
                "confidence": 0,
                "position": {
                    "x": 0,
                    "y": 0,
                    "w": 0,
                    "h": 0
                }
            }
            return json(body=match_data)
        
        match_data = {
            "tag": result[0],
            "confidence": result[1],
            "position": result[2]
        }

        return json(body=match_data)
    
    @threaded_request
    @app.post('/model/train')
    async def train(request: Request) -> HTTPResponse:
        try:
            faces = await database.all_faces(app.ctx.conn)
            app.ctx.model.train(faces)

            return json({"status": "ok"})
        except SanicException:
            return json({"status": "fail"})

    return app
