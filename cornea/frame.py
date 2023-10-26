from io import BytesIO
from typing import Union

import numpy as np
from numpy.typing import NDArray

_FRAME_T = Union[NDArray[np.uint8], bytes]


class Frame:
    """
    Class to represent a received frame of image data from the API.
    """
    def __init__(
            self,
            frame_data: _FRAME_T
    ):
        self.frame_data: _FRAME_T = frame_data
        if isinstance(self.frame_data, bytes):
            # convert the frame data into a numpy array if not already
            # converted.
            self.frame_data = np.frombuffer(self.frame_data, dtype=np.uint8)
        