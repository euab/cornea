from typing import Union, Tuple, Optional, List
from pathlib import Path
from io import BytesIO
import logging

from PIL import Image

import numpy as np
from numpy.typing import NDArray
import cv2
from cv2 import CascadeClassifier
from cv2.face import LBPHFaceRecognizer_create

from cornea.frame import Frame
from cornea.constants import MODEL_DEFAULT_PATH

HAAR_CASCADE_DATA = 'haarcascade_frontalface_default.xml'

logger = logging.getLogger(__name__)


class Model:
    def __init__(
            self,
            model_path: Union[str, Path],
    ) -> None:
        self.model_path = model_path
        self.classifier = CascadeClassifier(
            cv2.data.haarcascades + HAAR_CASCADE_DATA)
        self.recognizer = LBPHFaceRecognizer_create()

        self._load_model(self.model_path)
    
    def _load_model(self, model_path: Union[str, Path]) -> None:
        self.recognizer.read(model_path)
    
    def train(
            self,
            training_data: List[Tuple[bytes, int]],
            output_path: Optional[str] = None
        ) -> None:
        training_data = self.prepare_training_data(training_data)
        logger.info("Training OpenCV model, this may take a while.")
        self.recognizer.train(training_data[0], training_data[1])

        if output_path is None:
            output_path = MODEL_DEFAULT_PATH
        
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
