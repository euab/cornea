# SPDX-License-Identifier gpl2-only
#
# Copyright (C) 2023, Euan Mills. All Rights Reserved.
# This project is licesned under the GPL-2.0 License.
# See the file COPYING for more details.

import base64

from sanic import Sanic, response
from sanic.request import Request
from sanic.response import HTTPResponse, json

from cornea.model import Model
from cornea.frame import Frame
from cornea.constants import MODEL_DEFAULT_PATH

model: Model = Model(MODEL_DEFAULT_PATH)


def add_root_route(app: Sanic) -> None:
    @app.get('/')
    async def hello(request: Request) -> HTTPResponse:
        return response.text("Hello from Cornea version: 0.0.0-alpha1")


def create_server() -> Sanic:
    app = Sanic("cornea_server")
    add_root_route(app)

    @app.post('/detect_frame')
    async def detect_frame(request: Request):
        data = request.json
        decoded = base64.b64decode(bytes(data["frame"], encoding='utf8'))
        
        frame = Frame(decoded)
        result = await model.handle_frame(frame)

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

    return app
