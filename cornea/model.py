from typing import Union, Tuple, Optional
from pathlib import Path
import logging

import cv2
from cv2 import CascadeClassifier
from cv2.face import LBPHFaceRecognizer_create

from cornea.frame import Frame

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
    
    async def handle_frame(self, frame: Frame) -> Optional[Tuple[str, float, dict]]:
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
