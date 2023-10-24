from __future__ import annotations
from typing import Union, Tuple, Optional, List, Dict, Any
from pathlib import Path
from io import BytesIO
import logging
from datetime import datetime
import os

from PIL import Image

import numpy as np
from numpy.typing import NDArray
import cv2
from cv2 import CascadeClassifier
from cv2.face import LBPHFaceRecognizer_create

from cornea.frame import Frame

HAAR_CASCADE_DATA = 'haarcascade_frontalface_default.xml'

logger = logging.getLogger(__name__)


def get_latest_model_file(model_dir: str) -> str:
    models = [os.path.join(model_dir, basename) for basename \
              in os.listdir(model_dir)]
    return max(models, key=os.path.getctime)


def ensure_model_folder_exists(model_dir: str) -> None:
    if os.path.isdir(model_dir):
        return
    
    try:
        os.mkdir(model_dir)
    except OSError as e:
        logger.error(
            f"Unable to create models folder at: {model_dir}.\n{e}")
        raise RuntimeError(e)


class Model:
    def __init__(
            self,
            model_path: Optional[Union[str, Path]],
            config: Dict[Any, Any]
    ) -> None:
        self.model_path = model_path
        self.classifier = CascadeClassifier(
            cv2.data.haarcascades + HAAR_CASCADE_DATA)
        self.recognizer = LBPHFaceRecognizer_create()
        self.config = config

        self._load_model(self.model_path)
    
    def _load_model(
            self,
            model_path: Optional[Union[str, Path]] = None,
            latest: bool = True
        ) -> None:
        model_dir = self.config["model_default_path"]
        ensure_model_folder_exists(model_dir)
        if latest or model_path is None:
            model_path = get_latest_model_file(model_dir)

        self.recognizer.read(model_path)
    
    @classmethod
    def load_model(
        cls,
        model_path: Optional[Union[str, Path]],
        config: Dict[Any, Any]
    ) -> Model:
        return cls(model_path, config)
    
    def train(
            self,
            training_data: List[Tuple[bytes, int]],
            output_path: Optional[str] = None
        ) -> None:
        training_data = self.prepare_training_data(training_data)
        logger.info("Training OpenCV model, this may take a while.")
        self.recognizer.train(training_data[0], training_data[1])

        if output_path is None:
            output_path = self.format_model_path(
                self.config["model_default_path"])
        
        logger.info(f"Writing OpenCV model to: {output_path}")
        self.recognizer.write(output_path)

        logger.info(
            f"Reloading model for model: {self.model_path} -> {output_path}")
        self._load_model(output_path)
        self.model_path = output_path
    
    def prepare_training_data(
            self,
            training_data: List[Tuple[bytes, int]]
    ) -> Tuple[List[NDArray], List[NDArray]]:
        logger.info("Preparing OpenCV training data...")
        faces = []
        tags = []
        for entry in training_data:
            img = Image.open(BytesIO(entry[0])).convert('L')
            np_arr = np.array(img, 'uint8')

            found_faces = self.classifier.detectMultiScale(np_arr)
            for (x, y, w, h) in  found_faces:
                faces.append(np_arr[y:y+h, x:x+w])
                tags.append(entry[1])
        
        return faces, np.array(tags)
    
    async def handle_frame(self, frame: bytes) -> Optional[Tuple[str, float, dict]]:
        frame = Frame(frame)
        data = cv2.imdecode(frame.frame_data, cv2.IMREAD_GRAYSCALE)

        faces = self.classifier.detectMultiScale(
            data,
            scaleFactor=1.2,
            minNeighbors=5,
        )
        logger.debug("Faces detected: {}".format(faces))
        
        for (x, y, w, h) in faces:
            location = {"x": int(x), "y": int(y), "w": int(w), "h": int(h)}

            face_fingerprint, confidence = self.recognizer.predict(
                data[y:y+h, x:x+w]
            )
            confidence = 1 - (confidence / 100)

            logger.debug("Face hit: fingerprint: {} confidence: {} "
                         "(x: {}, y: {}, w: {}, h: {})".format(
                             face_fingerprint,
                             confidence,
                             location["x"],
                             location["y"],
                             location["w"],
                             location["h"]
                         ))

            return face_fingerprint, confidence, location
    
    def get_current_timestamp(self) -> str:
        dt_format = "%d_%m_%y_%H%M%S"
        return datetime.strftime(datetime.now(), dt_format)
    
    def format_model_path(self, model_dir: str) -> str:
        if not os.path.isdir(model_dir):
            raise RuntimeError('Model directory does not exist.')
        file_str = model_dir + "/cornea_cv_"
        file_str += self.get_current_timestamp() + '.yml'

        return os.path.abspath(file_str)
